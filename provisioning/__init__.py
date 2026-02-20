import re
import secrets
import asyncio

from .models import Customer
from . import db_setup, compute, dns, notify


async def provision(stripe_customer_id: str, subscription_id: str, email: str) -> None:
    """Orchestrate full customer provisioning. Called from Stripe webhook background task."""

    # Idempotency — don't double-provision if Stripe retries the webhook
    if Customer.select().where(Customer.stripe_customer_id == stripe_customer_id).exists():
        return

    slug        = _unique_slug(email)
    db_name     = f"crimata_{slug.replace('-', '_')}"
    db_password = secrets.token_urlsafe(24)
    secret_key  = secrets.token_hex(32)
    passphrase  = secrets.token_urlsafe(12)

    customer = Customer.create(
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=subscription_id,
        email=email,
        slug=slug,
        db_name=db_name,
        db_password=db_password,
        passphrase=passphrase,
        status="provisioning",
    )

    try:
        # 1. Create Postgres database on shared RDS
        await asyncio.to_thread(db_setup.create_database, db_name, db_password)

        # 2. Spin up ECS Fargate service + ALB routing
        await asyncio.to_thread(compute.create_service, slug, db_name, db_password, secret_key, passphrase)

        # 3. Create Route53 subdomain record
        await asyncio.to_thread(dns.create_record, slug)

        # 4. Send welcome email via SES
        await asyncio.to_thread(notify.send_welcome, email, slug, passphrase)

        customer.status = "active"
        customer.save()

    except Exception as e:
        customer.status = "failed"
        customer.save()
        print(f"Provisioning failed for {email}: {e}")
        raise


async def deprovision(stripe_customer_id: str) -> None:
    """Tear down all resources for a cancelled customer."""
    try:
        customer = Customer.get(Customer.stripe_customer_id == stripe_customer_id)
    except Customer.DoesNotExist:
        return

    customer.status = "cancelled"
    customer.save()

    await asyncio.to_thread(compute.delete_service, customer.slug, None)
    await asyncio.to_thread(db_setup.drop_database, customer.db_name)
    await asyncio.to_thread(dns.delete_record, customer.slug)


def _unique_slug(email: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", email.split("@")[0].lower()).strip("-")[:20]
    slug, suffix = base, 2
    while Customer.select().where(Customer.slug == slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug
