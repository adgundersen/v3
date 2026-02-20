import os
import stripe
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from dotenv import load_dotenv

import provisioning

load_dotenv()

stripe.api_key   = os.getenv("STRIPE_SECRET_KEY")
PRICE_ID         = os.getenv("STRIPE_PRICE_ID")
WEBHOOK_SECRET   = os.getenv("STRIPE_WEBHOOK_SECRET")
BASE_URL         = os.getenv("BASE_URL", "https://crimata.com")

router = APIRouter(prefix="/api/checkout", tags=["checkout"])


@router.post("/create-session")
async def create_session():
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": PRICE_ID, "quantity": 1}],
            success_url=f"{BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BASE_URL}/",
        )
        return {"url": session.url}
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        background_tasks.add_task(
            provisioning.provision,
            stripe_customer_id=session["customer"],
            subscription_id=session["subscription"],
            email=session["customer_details"]["email"],
        )

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        background_tasks.add_task(
            provisioning.deprovision,
            stripe_customer_id=sub["customer"],
        )

    return {"status": "ok"}
