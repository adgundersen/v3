import os
import boto3
from botocore.exceptions import ClientError

AWS_REGION     = os.getenv("AWS_REGION", "us-east-1")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL", "noreply@crimata.com")

ses = boto3.client("ses", region_name=AWS_REGION)


def send_welcome(email: str, slug: str, passphrase: str) -> None:
    url = f"https://{slug}.crimata.com"
    try:
        ses.send_email(
            Source=SES_FROM_EMAIL,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": "Your Crimata hub is ready"},
                "Body": {
                    "Text": {"Data": _text_body(url, passphrase)},
                    "Html": {"Data": _html_body(url, passphrase)},
                },
            },
        )
    except ClientError as e:
        # Don't fail provisioning over an email — log and move on
        print(f"SES send failed for {email}: {e}")


def _text_body(url: str, passphrase: str) -> str:
    return f"""Your Crimata hub is live.

URL: {url}
Passphrase: {passphrase}

Log in and change your passphrase in Settings.

— Crimata
"""


def _html_body(url: str, passphrase: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:480px;margin:40px auto;color:#111">
  <h2>Your hub is live.</h2>
  <p><a href="{url}">{url}</a></p>
  <p><strong>Passphrase:</strong> <code>{passphrase}</code></p>
  <p style="color:#555;font-size:0.9em">Log in and change your passphrase in Settings.</p>
  <p style="color:#999;font-size:0.85em">— Crimata</p>
</body>
</html>"""
