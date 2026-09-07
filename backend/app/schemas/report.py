"""Read-only report and dashboard response models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel


class ExportFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"


class AmountPoint(BaseModel):
    label: str
    amount: Decimal


class HourlyAmountPoint(BaseModel):
    hour: int
    amount: Decimal


class CollectorAmountPoint(BaseModel):
    collector_id: str
    collector_name: str
    transactions: int
    amount: Decimal


class TransactionStatusPoint(BaseModel):
    status: str
    transactions: int
    amount: Decimal


class GiftCategoryPoint(BaseModel):
    gift_type: str
    quantity: int


class DashboardSummary(BaseModel):
    total_guests: int
    total_contributions: Decimal
    total_cash: Decimal
    total_online: Decimal
    total_gift_items: int
    verified_amount: Decimal
    pending_amount: Decimal
    collectors: int
    unreconciled_amount: Decimal


class DashboardData(DashboardSummary):
    contributions_over_time: list[AmountPoint]
    cash_vs_online: list[AmountPoint]
    collector_wise_collection: list[CollectorAmountPoint]
    transaction_status: list[TransactionStatusPoint]
    gift_categories: list[GiftCategoryPoint]
    hourly_collection: list[HourlyAmountPoint]


class EventReport(DashboardData):
    event_id: str
    event_name: str
    event_date: datetime


class CollectorReport(BaseModel):
    collector_id: str
    collector_name: str
    transactions: int
    cash: Decimal
    online: Decimal
    total: Decimal
    pending: Decimal
    mismatch: Decimal


class GuestReportItem(BaseModel):
    guest_id: str
    full_name: str
    family_name: str
    relationship: str
    contribution: Decimal
    gift_items: int
    gift_estimated_value: Decimal


class ReconciliationReportItem(BaseModel):
    reconciliation_id: str
    event_id: str
    collector_id: str
    collector_name: str
    expected_cash: Decimal
    actual_cash: Decimal
    difference: Decimal
    status: str
    submitted_at: datetime
    verified_at: datetime | None = None
    resolved_at: datetime | None = None
