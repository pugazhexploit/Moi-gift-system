"""Strict financial transaction request and response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PaymentMethod(StrEnum):
    CASH = "cash"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    OTHER = "other"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    LOCKED = "locked"


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(pattern=r"^EVT-\d{6,}$")
    guest_id: str = Field(pattern=r"^GST-\d{6,}$")
    collector_id: str | None = Field(default=None, pattern=r"^COL-\d{6,}$")
    amount: Decimal = Field(gt=Decimal("0"), max_digits=18, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    payment_method: PaymentMethod
    reference_number: str | None = Field(default=None, max_length=100)
    notes: str = Field(default="", max_length=1_000)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def reference_required_for_non_cash(self) -> "TransactionCreate":
        if self.payment_method is not PaymentMethod.CASH and not self.reference_number:
            raise ValueError("Reference number is required for non-cash payments")
        return self


class TransactionAction(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reason: str = Field(default="", max_length=500)


class TransactionResponse(BaseModel):
    transaction_id: str
    event_id: str
    guest_id: str
    collector_id: str
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    transaction_type: str
    status: TransactionStatus
    reference_number: str | None
    notes: str
    created_at: datetime
    updated_at: datetime
    verified_at: datetime | None = None
    locked_at: datetime | None = None


class ReceiptResponse(BaseModel):
    receipt_id: str
    transaction_id: str
    issued_at: datetime
    verification_status: str


class TransactionCreateData(BaseModel):
    transaction: TransactionResponse
    receipt: ReceiptResponse
    receipt_verification_token: str | None


class ReceiptVerificationResponse(BaseModel):
    receipt_id: str
    verification_status: str
