"""Strict request and response models for physical gifts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GiftStatus(StrEnum):
    RECEIVED = "received"
    CANCELLED = "cancelled"


class GiftCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(pattern=r"^EVT-\d{6,}$")
    guest_id: str = Field(pattern=r"^GST-\d{6,}$")
    collector_id: str | None = Field(default=None, pattern=r"^COL-\d{6,}$")
    gift_type: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_-]+$")
    description: str = Field(min_length=2, max_length=500)
    quantity: int = Field(default=1, ge=1, le=10_000)
    estimated_value: Decimal | None = Field(default=None, gt=Decimal("0"), max_digits=18, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    notes: str = Field(default="", max_length=1_000)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class GiftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    gift_type: str | None = Field(default=None, min_length=2, max_length=80, pattern=r"^[a-z0-9_-]+$")
    description: str | None = Field(default=None, min_length=2, max_length=500)
    quantity: int | None = Field(default=None, ge=1, le=10_000)
    estimated_value: Decimal | None = Field(default=None, gt=Decimal("0"), max_digits=18, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    notes: str | None = Field(default=None, max_length=1_000)
    status: GiftStatus | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class GiftResponse(BaseModel):
    gift_id: str
    event_id: str
    guest_id: str
    collector_id: str
    gift_type: str
    description: str
    quantity: int
    estimated_value: Decimal | None
    currency: str
    notes: str
    status: GiftStatus
    created_at: datetime
    updated_at: datetime
