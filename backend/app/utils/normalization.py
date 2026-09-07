"""Safe normalization helpers used for indexed lookups and duplicate checks."""

from __future__ import annotations

import re


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return digits or None
