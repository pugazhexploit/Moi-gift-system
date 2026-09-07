"""Password, token, and CSRF primitives for browser authentication."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type

from app.core.config import Settings
from app.models.user import UserRole


password_hasher = PasswordHasher(type=Type.ID)


class InvalidTokenError(Exception):
    """Raised when an access token is expired, malformed, or incorrectly scoped."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return password_hasher.check_needs_rehash(password_hash)


def create_access_token(settings: Settings, user_id: str, role: UserRole) -> str:
    access_secret, _ = settings.auth_secrets()
    issued_at = utc_now()
    payload = {
        "sub": user_id,
        "role": role.value,
        "type": "access",
        "jti": str(uuid4()),
        "iat": issued_at,
        "nbf": issued_at,
        "exp": issued_at + timedelta(minutes=settings.access_token_expire_minutes),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    return jwt.encode(payload, access_secret, algorithm="HS256")


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    access_secret, _ = settings.auth_secrets()
    try:
        payload = jwt.decode(token, access_secret, algorithms=["HS256"], issuer=settings.jwt_issuer, audience=settings.jwt_audience, options={"require": ["sub", "type", "exp", "iat", "jti"]})
    except jwt.PyJWTError as exc:
        raise InvalidTokenError from exc
    if payload.get("type") != "access":
        raise InvalidTokenError
    return payload


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(settings: Settings, token: str) -> str:
    _, refresh_secret = settings.auth_secrets()
    return hmac.new(refresh_secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_receipt_token(settings: Settings, token: str) -> str:
    """Hash opaque public receipt-verification tokens with a server secret."""
    return hash_refresh_token(settings, token)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_tokens_match(header_token: str | None, cookie_token: str | None) -> bool:
    return bool(header_token and cookie_token and hmac.compare_digest(header_token, cookie_token))
