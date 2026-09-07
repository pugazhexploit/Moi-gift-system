"""Opaque QR and human-readable identifier helpers."""

from __future__ import annotations

import secrets


def generate_qr_token() -> str:
    """Generate an opaque token with no embedded guest or financial data."""
    return secrets.token_urlsafe(32)


def format_sequence_id(prefix: str, sequence: int) -> str:
    return f"{prefix}-{sequence:06d}"
