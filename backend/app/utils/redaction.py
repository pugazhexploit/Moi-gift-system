"""Utilities for preventing secrets from reaching application logs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SENSITIVE_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "jwt_secret",
        "jwt_refresh_secret",
        "otp",
        "secret",
    }
)


def redact(value: Any) -> Any:
    """Return a recursively redacted copy suitable for structured logging."""
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if str(key).lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value
