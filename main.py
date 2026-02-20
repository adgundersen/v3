from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import db
from models import Profile, Post, PostImage, Tag, PostTag
from provisioning.models import Customer
from routers import auth, profile, posts, checkout, health

STATIC_DIR    = Path(__file__).parent / "static"
UPLOAD_DIR    = STATIC_DIR / "uploads"
FRONTEND_DIR  = Path(__file__).parent / "public"
MARKETING_DIR = Path(__file__).parent / "marketing"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect(reuse_if_open=True)
    db.create_tables([Profile, Post, PostImage, Tag, PostTag, Customer], safe=True)
    db.close()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Crimata", lifespan=lifespan)

# 1. Static file mounts (must come before catch-all)
app.mount("/uploads",   StaticFiles(directory=str(UPLOAD_DIR)),    name="uploads")
app.mount("/assets",    StaticFiles(directory=str(FRONTEND_DIR)),  name="public-assets")
app.mount("/marketing", StaticFiles(directory=str(MARKETING_DIR)), name="marketing")

# 2. API routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(posts.router)
app.include_router(checkout.router)


# 3. Marketing routes
@app.get("/", include_in_schema=False)
async def homepage():
    return FileResponse(str(MARKETING_DIR / "index.html"))

@app.get("/success", include_in_schema=False)
async def success():
    return FileResponse(str(MARKETING_DIR / "success.html"))


# 4. SPA catch-all — MUST be last
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    return FileResponse(str(FRONTEND_DIR / "index.html"))
