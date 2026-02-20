from fastapi import APIRouter, HTTPException, status
from schemas import TokenRequest, TokenResponse
from auth import verify_passphrase, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(body: TokenRequest):
    if not verify_passphrase(body.passphrase):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong passphrase")
    return TokenResponse(access_token=create_access_token())
