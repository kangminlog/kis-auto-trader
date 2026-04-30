from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.auth import create_access_token, hash_password, verify_password
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SetupRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    if not settings.admin_password_hash:
        raise HTTPException(status_code=400, detail="Admin account not set up. Use /api/auth/setup first.")

    if req.username != settings.admin_username:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(req.password, settings.admin_password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(req.username)
    return TokenResponse(access_token=token)


@router.post("/setup", response_model=TokenResponse)
def setup(req: SetupRequest):
    """초기 관리자 계정 설정. 이미 설정된 경우 거부."""
    if settings.admin_password_hash:
        raise HTTPException(status_code=400, detail="Admin already configured")

    settings.admin_username = req.username
    settings.admin_password_hash = hash_password(req.password)

    token = create_access_token(req.username)
    return TokenResponse(access_token=token)
