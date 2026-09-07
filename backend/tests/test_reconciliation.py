"""Regression tests for Phase 6 reconciliation invariants."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from bson.decimal128 import Decimal128
from pydantic import ValidationError

from app.schemas.reconciliation import ReconciliationCreate, ReconciliationStatus
from app.services.reconciliation_service import ReconciliationService


def test_reconciliation_accepts_zero_actual_cash() -> None:
    reconciliation = ReconciliationCreate(
        event_id="EVT-000001",
        actual_cash=Decimal("0.00"),
    )

    assert reconciliation.actual_cash == Decimal("0.00")


def test_reconciliation_rejects_negative_actual_cash() -> None:
    with pytest.raises(ValidationError):
        ReconciliationCreate(event_id="EVT-000001", actual_cash=Decimal("-0.01"))


def test_reconciliation_response_uses_decimal_values_and_public_ids() -> None:
    response = ReconciliationService.to_response(
        {
            "reconciliation_id": "REC-000001",
            "event_public_id": "EVT-000001",
            "collector_public_id": "COL-000001",
            "expected_cash": Decimal128("5000.00"),
            "actual_cash": Decimal128("4950.00"),
            "difference": Decimal128("-50.00"),
            "reason": "A counted note was damaged.",
            "status": ReconciliationStatus.MISMATCH.value,
            "submitted_at": datetime.now(timezone.utc),
        }
    )

    assert response.event_id == "EVT-000001"
    assert response.collector_id == "COL-000001"
    assert response.difference == Decimal("-50.00")
