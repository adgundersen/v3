from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Profile ──────────────────────────────────────────────────────────────────

class LinkItem(BaseModel):
    label: str
    url: str


class ProfileRead(BaseModel):
    id: int
    name: str
    bio: str
    avatar_filename: Optional[str]
    links: list[LinkItem]

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    links: Optional[list[LinkItem]] = None


# ── Tags ─────────────────────────────────────────────────────────────────────

class TagRead(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# ── PostImage ─────────────────────────────────────────────────────────────────

class PostImageRead(BaseModel):
    id: int
    filename: str
    order: int

    model_config = {"from_attributes": True}


# ── Post ──────────────────────────────────────────────────────────────────────

class PostCreate(BaseModel):
    caption: str = ""
    location: Optional[str] = None
    published: bool = False
    tags: list[str] = []


class PostUpdate(BaseModel):
    caption: Optional[str] = None
    location: Optional[str] = None
    published: Optional[bool] = None
    tags: Optional[list[str]] = None


class PostRead(BaseModel):
    id: int
    caption: str
    location: Optional[str]
    published: bool
    created_at: datetime
    images: list[PostImageRead]
    tags: list[TagRead]

    model_config = {"from_attributes": True}


# ── Image reorder ─────────────────────────────────────────────────────────────

class ReorderImages(BaseModel):
    image_ids: list[int]


# ── Auth ──────────────────────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    passphrase: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
