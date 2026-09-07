"""Regression tests for dashboard aggregation mapping and export safety."""

from __future__ import annotations

from bson.decimal128 import Decimal128

from app.services.export_service import ExportService
from app.services.report_service import ReportService


def test_dashboard_mapping_excludes_rejected_amounts_from_totals() -> None:
    service = object.__new__(ReportService)
    dashboard = service._dashboard_from_raw(
        {
            "transactions": {
                "totals": [
                    {
                        "total_contributions": Decimal128("500.00"),
                        "total_cash": Decimal128("300.00"),
                        "total_online": Decimal128("200.00"),
                        "verified_amount": Decimal128("200.00"),
                        "pending_amount": Decimal128("300.00"),
                    }
                ],
                "transaction_status": [
                    {"_id": "pending", "transactions": 1, "amount": Decimal128("300.00")},
                    {"_id": "rejected", "transactions": 1, "amount": Decimal128("100.00")},
                ],
            },
            "total_guests": 2,
            "gifts": {"totals": [{"quantity": 3}], "categories": []},
            "collectors": 1,
            "unreconciled_amount": Decimal128("25.00"),
        }
    )

    assert str(dashboard.total_contributions) == "500.00"
    assert [item.status for item in dashboard.transaction_status] == ["pending", "rejected"]


def test_csv_export_neutralizes_spreadsheet_formula_text() -> None:
    export = ExportService()._csv("guest-report", ["Guest"], [["=HYPERLINK(\"bad\")"]])

    assert b"'=HYPERLINK" in export.content
