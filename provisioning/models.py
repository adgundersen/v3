import datetime
from peewee import Model, CharField, DateTimeField
from database import db


class Customer(Model):
    stripe_customer_id   = CharField(unique=True)
    stripe_subscription_id = CharField(unique=True)
    email                = CharField()
    slug                 = CharField(unique=True)   # subdomain: slug.crimata.com
    db_name              = CharField(unique=True)
    db_password          = CharField()              # password for customer's RDS user
    passphrase           = CharField()              # initial login passphrase
    status               = CharField(default="provisioning")  # provisioning | active | failed | cancelled
    created_at           = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        database = db
        table_name = "customers"
