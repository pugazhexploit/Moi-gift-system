"""Strict request and response models for cash reconciliation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReconciliationStatus(StrEnum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    MISMATCH = "mismatch"
    RESOLVED = "resolved"


class ReconciliationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(pattern=r"^EVT-\d{6,}$")
    collector_id: str | None = Field(default=None, pattern=r"^COL-\d{6,}$")
    actual_cash: Decimal = Field(ge=Decimal("0"), max_digits=18, decimal_places=2)
    reason: str = Field(default="", max_length=1_000)


class ReconciliationAction(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reason: str = Field(default="", max_length=1_000)


class ReconciliationResponse(BaseModel):
    reconciliation_id: str
    event_id: str
    collector_id: str
    expected_cash: Decimal
    actual_cash: Decimal
    difference: Decimal
    reason: str
    status: ReconciliationStatus
    submitted_at: datetime
    verified_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_note: str | None = None


class ReconciliationCreateData(BaseModel):
    reconciliation: ReconciliationResponse
