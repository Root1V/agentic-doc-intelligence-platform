"""POST /auth/login — the only unauthenticated route besides /health.
No self-signup: users are created via ``scripts/create_user.py`` (internal
tool, no evidence of needing public registration)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from idp.api.deps import get_app_settings, get_db_session
from idp.auth.security import create_access_token, verify_password
from idp.config import Settings
from idp.persistence.repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> LoginResponse:
    user = await UserRepository(session).get_by_email(body.email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")
    token = create_access_token(settings, user_id=user.id)
    return LoginResponse(access_token=token, user_name=user.name, role=user.role)
