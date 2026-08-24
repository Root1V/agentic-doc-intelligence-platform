"""Password hashing and JWT issuance/verification for the internal-tool
login (replaces the static ``x-api-key`` used before the frontend module —
see the plan's 'Login real, no una pantalla decorativa' decision).

HS256 with a single shared secret is adequate here: one backend process
issues and verifies its own tokens, no second service needs to verify them
independently. Move to asymmetric keys only if that changes.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from idp.config import Settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_access_token(settings: Settings, *, user_id: uuid.UUID) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(settings: Settings, token: str) -> uuid.UUID | None:
    """Returns the user id encoded in a valid, unexpired token, or None if
    the token is missing/invalid/expired — callers turn None into a 401,
    this module has no opinion on HTTP."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    subject = payload.get("sub")
    if subject is None:
        return None
    try:
        return uuid.UUID(subject)
    except ValueError:
        return None
