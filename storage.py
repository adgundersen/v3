import os
import shutil
from pathlib import Path

import boto3
from fastapi import UploadFile

APP_ENV    = os.getenv("APP_ENV", "dev")
S3_BUCKET  = os.getenv("S3_BUCKET")
S3_REGION  = os.getenv("AWS_REGION", "us-east-1")
UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"

_s3 = boto3.client("s3", region_name=S3_REGION) if APP_ENV == "prod" else None


def upload(file: UploadFile, filename: str) -> None:
    if APP_ENV == "prod":
        _s3.upload_fileobj(
            file.file, S3_BUCKET, filename,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
    else:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        with (UPLOAD_DIR / filename).open("wb") as f:
            shutil.copyfileobj(file.file, f)


def delete(filename: str) -> None:
    if APP_ENV == "prod":
        _s3.delete_object(Bucket=S3_BUCKET, Key=filename)
    else:
        path = UPLOAD_DIR / filename
        if path.exists():
            path.unlink()


def public_url(filename: str | None) -> str | None:
    if not filename:
        return None
    if APP_ENV == "prod":
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"
    return f"/uploads/{filename}"
