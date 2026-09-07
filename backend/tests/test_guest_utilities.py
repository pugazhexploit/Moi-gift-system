"""Guest search and QR helpers must never encode private data."""

from __future__ import annotations

from app.utils.identifiers import generate_qr_token
from app.utils.normalization import normalize_phone, normalize_text


def test_normalization_is_stable_for_duplicate_detection() -> None:
    assert normalize_text("  Ananya   Rao ") == "ananya rao"
    assert normalize_phone("+91 (987) 654-3210") == "919876543210"


def test_qr_token_is_opaque_and_does_not_contain_guest_data() -> None:
    token = generate_qr_token()
    assert len(token) >= 40
    assert "guest" not in token.casefold()
    assert "@" not in token
