"""Tests for authentication primitives that do not require MongoDB."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.security import InvalidTokenError, create_access_token, csrf_tokens_match, decode_access_token, hash_password, hash_refresh_token, verify_password
from app.models.user import UserRole


@pytest.fixture
def settings() -> Settings:
    return Settings(jwt_secret="a" * 48, jwt_refresh_secret="b" * 48, mongodb_uri="mongodb://localhost:27017")


def test_argon2_passwords_are_verified_without_plaintext_storage() -> None:
    password_hash = hash_password("a-strong-development-password")
    assert password_hash.startswith("$argon2id$")
    assert verify_password("a-strong-development-password", password_hash)
    assert not verify_password("incorrect-password", password_hash)


def test_access_token_has_expected_scope(settings: Settings) -> None:
    token = create_access_token(settings, "507f1f77bcf86cd799439011", UserRole.ADMIN)
    decoded = decode_access_token(settings, token)
    assert decoded["sub"] == "507f1f77bcf86cd799439011"
    assert decoded["type"] == "access"


def test_refresh_token_hash_is_keyed_and_csrf_is_constant_time_checked(settings: Settings) -> None:
    assert hash_refresh_token(settings, "refresh-token") != "refresh-token"
    assert csrf_tokens_match("csrf-token", "csrf-token")
    assert not csrf_tokens_match("csrf-token", "different-token")


def test_wrong_secret_rejects_access_token(settings: Settings) -> None:
    token = create_access_token(settings, "507f1f77bcf86cd799439011", UserRole.ADMIN)
    different_settings = Settings(jwt_secret="c" * 48, jwt_refresh_secret="b" * 48, mongodb_uri="mongodb://localhost:27017")
    with pytest.raises(InvalidTokenError):
        decode_access_token(different_settings, token)
