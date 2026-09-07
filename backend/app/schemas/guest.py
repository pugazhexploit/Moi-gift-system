"""Guest requests and safe API views."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Address(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    line_1: str = Field(default="", max_length=200)
    line_2: str = Field(default="", max_length=200)
    city: str = Field(default="", max_length=100)
    district: str = Field(default="", max_length=100)
    state: str = Field(default="", max_length=100)
    postal_code: str = Field(default="", max_length=20)
    country: str = Field(default="", max_length=100)


class GuestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(pattern=r"^EVT-\d{6,}$")
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(default="", max_length=32)
    email: EmailStr | None = None
    address: Address = Field(default_factory=Address)
    relationship: str = Field(default="", max_length=100)
    family_name: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=1_000)


class GuestUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    address: Address | None = None
    relationship: str | None = Field(default=None, max_length=100)
    family_name: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=1_000)


class GuestResponse(BaseModel):
    guest_id: str
    event_id: str
    full_name: str
    phone: str
    email: EmailStr | None
    address: Address
    relationship: str
    family_name: str
    notes: str
    created_at: datetime
    updated_at: datetime


class GuestQrResponse(BaseModel):
    guest_id: str
    qr_token: str
