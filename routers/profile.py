import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

import storage
from database import db
from models import Profile
from schemas import ProfileRead, ProfileUpdate
from auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _profile_to_dict(profile: Profile) -> dict:
    return {
        "id": profile.id,
        "name": profile.name,
        "bio": profile.bio,
        "avatar_filename": profile.avatar_filename,
        "avatar_url": storage.public_url(profile.avatar_filename),
        "links": profile.links or [],
    }


def _get_or_create_profile() -> Profile:
    profile = Profile.get_or_none()
    if profile is None:
        profile = Profile.create(name="", bio="", links=[])
    return profile


@router.get("", response_model=ProfileRead)
def get_profile():
    with db.connection_context():
        return _profile_to_dict(_get_or_create_profile())


@router.patch("", response_model=ProfileRead)
def update_profile(
    body: ProfileUpdate,
    _: str = Depends(get_current_user),
):
    with db.connection_context():
        profile = _get_or_create_profile()
        if body.name is not None:
            profile.name = body.name
        if body.bio is not None:
            profile.bio = body.bio
        if body.links is not None:
            profile.links = [link.model_dump() for link in body.links]
        profile.save()
        return _profile_to_dict(profile)


@router.post("/avatar", response_model=ProfileRead)
def upload_avatar(
    file: UploadFile = File(...),
    _: str = Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext!r} not allowed")

    with db.connection_context():
        profile = _get_or_create_profile()

        if profile.avatar_filename:
            storage.delete(profile.avatar_filename)

        filename = f"{uuid.uuid4()}{ext}"
        storage.upload(file, filename)

        profile.avatar_filename = filename
        profile.save()
        return _profile_to_dict(profile)
