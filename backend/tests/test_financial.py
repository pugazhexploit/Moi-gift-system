"""Regression tests for Phase 5 financial invariants."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.transaction import PaymentMethod, TransactionCreate
from app.services.transaction_service import TransactionService
from app.utils.money import from_decimal128, to_decimal128


def transaction_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_id": "EVT-000001",
        "guest_id": "GST-000001",
        "collector_id": "COL-000001",
        "amount": "5000.00",
        "payment_method": PaymentMethod.CASH,
    }
    payload.update(overrides)
    return payload


def test_money_round_trips_through_decimal128() -> None:
    value = Decimal("5000.005")

    assert from_decimal128(to_decimal128(value)) == Decimal("5000.01")


def test_non_cash_payment_requires_reference_number() -> None:
    with pytest.raises(ValidationError):
        TransactionCreate(**transaction_payload(payment_method=PaymentMethod.UPI))

    transaction = TransactionCreate(
        **transaction_payload(payment_method=PaymentMethod.UPI, reference_number="UPI-123")
    )
    assert transaction.reference_number == "UPI-123"


def test_receipt_response_uses_public_transaction_id() -> None:
    response = TransactionService.receipt_response(
        {
            "receipt_id": "RCP-000001",
            "transaction_id": "507f1f77bcf86cd799439011",
            "transaction_public_id": "TXN-000001",
            "issued_at": datetime.now(timezone.utc),
            "verification_status": "valid",
        }
    )

    assert response.transaction_id == "TXN-000001"
