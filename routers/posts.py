import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

import storage
from database import db
from models import Post, PostImage, Tag, PostTag
from schemas import PostCreate, PostUpdate, PostRead, ReorderImages
from auth import get_current_user

router = APIRouter(prefix="/api/posts", tags=["posts"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _serialize_post(post_id: int) -> dict:
    post = Post.get_or_none(Post.id == post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    images = list(
        PostImage.select()
        .where(PostImage.post == post_id)
        .order_by(PostImage.order)
    )
    tags = list(
        Tag.select()
        .join(PostTag)
        .where(PostTag.post == post_id)
    )
    return {
        "id": post.id,
        "caption": post.caption,
        "location": post.location,
        "published": post.published,
        "created_at": post.created_at,
        "images": [
            {"id": img.id, "filename": img.filename, "url": storage.public_url(img.filename), "order": img.order}
            for img in images
        ],
        "tags": [{"id": tag.id, "name": tag.name} for tag in tags],
    }


def _resolve_tags(tag_names: list[str]) -> list[Tag]:
    tags = []
    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        tag, _ = Tag.get_or_create(name=name)
        tags.append(tag)
    return tags


def _get_post_or_404(post_id: int, published_only: bool = False) -> Post:
    q = Post.select().where(Post.id == post_id)
    if published_only:
        q = q.where(Post.published == True)  # noqa: E712
    post = q.get_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


def _batch_serialize(posts: list[Post]) -> list[dict]:
    if not posts:
        return []
    ids = [p.id for p in posts]
    imgs = (PostImage.select()
            .where(PostImage.post << ids)
            .order_by(PostImage.order))
    pts = (PostTag.select(PostTag, Tag)
           .join(Tag)
           .where(PostTag.post << ids))

    img_map: dict[int, list] = {pid: [] for pid in ids}
    for img in imgs:
        img_map[img.post_id].append({
            "id": img.id,
            "filename": img.filename,
            "url": storage.public_url(img.filename),
            "order": img.order,
        })

    tag_map: dict[int, list] = {pid: [] for pid in ids}
    for pt in pts:
        tag_map[pt.post_id].append({"id": pt.tag.id, "name": pt.tag.name})

    return [
        {
            "id": p.id,
            "caption": p.caption,
            "location": p.location,
            "published": p.published,
            "created_at": p.created_at,
            "images": img_map[p.id],
            "tags": tag_map[p.id],
        }
        for p in posts
    ]


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=list[PostRead])
def list_posts(tag: Optional[str] = Query(None)):
    with db.connection_context():
        if tag:
            tag_name = tag.strip().lower()
            posts = list(
                Post.select()
                .join(PostTag)
                .join(Tag)
                .where(Post.published == True, Tag.name == tag_name)  # noqa: E712
                .order_by(Post.created_at.desc())
            )
        else:
            posts = list(
                Post.select()
                .where(Post.published == True)  # noqa: E712
                .order_by(Post.created_at.desc())
            )
        return _batch_serialize(posts)


@router.get("/feed/all", response_model=list[PostRead])
def list_all_posts(_: str = Depends(get_current_user)):
    with db.connection_context():
        posts = list(Post.select().order_by(Post.created_at.desc()))
        return _batch_serialize(posts)


@router.get("/{post_id}", response_model=PostRead)
def get_post(post_id: int):
    with db.connection_context():
        _get_post_or_404(post_id, published_only=True)
        return _serialize_post(post_id)


# ── Owner endpoints ───────────────────────────────────────────────────────────

@router.post("", response_model=PostRead, status_code=201)
def create_post(
    body: PostCreate,
    _: str = Depends(get_current_user),
):
    with db.connection_context():
        tags = _resolve_tags(body.tags)
        post = Post.create(
            caption=body.caption,
            location=body.location,
            published=body.published,
        )
        if tags:
            PostTag.insert_many([{"post": post.id, "tag": t.id} for t in tags]).execute()
        return _serialize_post(post.id)


@router.patch("/{post_id}", response_model=PostRead)
def update_post(
    post_id: int,
    body: PostUpdate,
    _: str = Depends(get_current_user),
):
    with db.connection_context():
        post = _get_post_or_404(post_id)
        if body.caption is not None:
            post.caption = body.caption
        if body.location is not None:
            post.location = body.location
        if body.published is not None:
            post.published = body.published
        if body.tags is not None:
            PostTag.delete().where(PostTag.post == post).execute()
            tags = _resolve_tags(body.tags)
            if tags:
                PostTag.insert_many([{"post": post.id, "tag": t.id} for t in tags]).execute()
        post.save()
        return _serialize_post(post_id)


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    _: str = Depends(get_current_user),
):
    with db.connection_context():
        post = _get_post_or_404(post_id)
        for img in PostImage.select().where(PostImage.post == post_id):
            storage.delete(img.filename)
        post.delete_instance(recursive=True)


# ── Image management ──────────────────────────────────────────────────────────

@router.post("/{post_id}/images", response_model=PostRead)
def upload_images(
    post_id: int,
    files: list[UploadFile] = File(...),
    _: str = Depends(get_current_user),
):
    with db.connection_context():
        _get_post_or_404(post_id)
        existing = list(PostImage.select().where(PostImage.post == post_id).order_by(PostImage.order))
        next_order = max((img.order for img in existing), default=-1) + 1

        for file in files:
            ext = Path(file.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail=f"File type {ext!r} not allowed")
            filename = f"{uuid.uuid4()}{ext}"
            storage.upload(file, filename)
            PostImage.create(post=post_id, filename=filename, order=next_order)
            next_order += 1

        return _serialize_post(post_id)


@router.delete("/{post_id}/images/{image_id}", response_model=PostRead)
def delete_image(
    post_id: int,
    image_id: int,
    _: str = Depends(get_current_user),
):
    with db.connection_context():
        _get_post_or_404(post_id)
        img = PostImage.get_or_none(PostImage.id == image_id, PostImage.post == post_id)
        if img is None:
            raise HTTPException(status_code=404, detail="Image not found")
        storage.delete(img.filename)
        img.delete_instance()
        return _serialize_post(post_id)


@router.patch("/{post_id}/images/reorder", response_model=PostRead)
def reorder_images(
    post_id: int,
    body: ReorderImages,
    _: str = Depends(get_current_user),
):
    with db.connection_context():
        _get_post_or_404(post_id)
        images = list(PostImage.select().where(PostImage.post == post_id))
        id_to_img = {img.id: img for img in images}
        for order, image_id in enumerate(body.image_ids):
            if image_id in id_to_img:
                img = id_to_img[image_id]
                img.order = order
                img.save()
        return _serialize_post(post_id)
