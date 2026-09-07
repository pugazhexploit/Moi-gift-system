"""Authoritative, event-scoped dashboard reports and audited exports."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from bson.decimal128 import Decimal128

from app.core.exceptions import AppError
from app.models.user import UserRole
from app.repositories.collectors import CollectorRepository
from app.repositories.reports import ReportRepository
from app.schemas.report import (
    AmountPoint,
    CollectorAmountPoint,
    CollectorReport,
    DashboardData,
    EventReport,
    ExportFormat,
    GiftCategoryPoint,
    GuestReportItem,
    HourlyAmountPoint,
    ReconciliationReportItem,
    TransactionStatusPoint,
)
from app.services.audit_service import AuditService
from app.services.event_access_service import EventAccessService
from app.services.export_service import ExportFile, ExportService
from app.utils.money import from_decimal128


class ReportService:
    MAX_EXPORT_ROWS = 10_000

    def __init__(self, database: Any) -> None:
        self.collectors = CollectorRepository(database)
        self.reports = ReportRepository(database)
        self.access = EventAccessService(database)
        self.audit = AuditService(database)
        self.exports = ExportService()

    async def dashboard(
        self,
        user: dict[str, Any],
        event_id: str | None,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> DashboardData:
        self._validate_dates(start_at, end_at)
        event_ids = await self._event_scope(user, event_id)
        return self._dashboard_from_raw(await self.reports.dashboard(event_ids, start_at, end_at))

    async def event_report(self, event_id: str, user: dict[str, Any]) -> EventReport:
        event = await self.access.event_for_user(event_id, user)
        dashboard = self._dashboard_from_raw(await self.reports.dashboard([event["_id"]], None, None))
        return EventReport(
            event_id=event["event_id"],
            event_name=event["event_name"],
            event_date=event["event_date"],
            **dashboard.model_dump(),
        )

    async def collector_report(
        self, collector_id: str, user: dict[str, Any], event_id: str | None
    ) -> CollectorReport:
        collector = await self.collectors.get_by_public_id(collector_id)
        if collector is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        role = UserRole(user["role"])
        if role is UserRole.COLLECTOR:
            own_collector = await self.collectors.get_by_user_id(user["_id"])
            if own_collector is None or own_collector["_id"] != collector["_id"]:
                raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        if role is UserRole.VIEWER:
            if not event_id:
                raise AppError("VALIDATION_ERROR", "event_id is required for viewer collector reports", 422)
            event = await self.access.event_for_user(event_id, user)
            if not await self.collectors.is_assigned(event["_id"], collector["_id"]):
                raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        metrics = await self.reports.collector_report(
            collector["_id"], await self._event_scope(user, event_id)
        )
        return CollectorReport(
            collector_id=collector["collector_id"],
            collector_name=collector["name"],
            transactions=int(metrics.get("transactions", 0)),
            cash=self._amount(metrics.get("cash")),
            online=self._amount(metrics.get("online")),
            total=self._amount(metrics.get("total")),
            pending=self._amount(metrics.get("pending")),
            mismatch=self._amount(metrics.get("mismatch")),
        )

    async def guest_report(
        self, user: dict[str, Any], event_id: str | None, page: int, limit: int
    ) -> tuple[list[GuestReportItem], int]:
        items, total = await self.reports.guest_report(
            await self._event_scope(user, event_id), page, limit
        )
        return [self._guest_item(item) for item in items], total

    async def reconciliation_report(
        self, user: dict[str, Any], event_id: str | None, page: int, limit: int
    ) -> tuple[list[ReconciliationReportItem], int]:
        items, total = await self.reports.reconciliation_report(
            await self._event_scope(user, event_id), page, limit
        )
        return [self._reconciliation_item(item) for item in items], total

    async def export_event(
        self,
        event_id: str,
        export_format: ExportFormat,
        user: dict[str, Any],
        context: dict[str, str | None],
    ) -> ExportFile:
        report = await self.event_report(event_id, user)
        rows = [
            ["Total guests", report.total_guests],
            ["Total contributions", report.total_contributions],
            ["Total cash", report.total_cash],
            ["Total online", report.total_online],
            ["Total gift items", report.total_gift_items],
            ["Verified amount", report.verified_amount],
            ["Pending amount", report.pending_amount],
            ["Collectors", report.collectors],
            ["Unreconciled amount", report.unreconciled_amount],
        ]
        result = await self.exports.build(
            export_format, f"event-report-{event_id}", ["Metric", "Value"], rows
        )
        event = await self.access.event_for_user(event_id, user)
        await self._audit_export(user, context, "event", export_format, event["_id"])
        return result

    async def export_collector(
        self,
        collector_id: str,
        event_id: str | None,
        export_format: ExportFormat,
        user: dict[str, Any],
        context: dict[str, str | None],
    ) -> ExportFile:
        report = await self.collector_report(collector_id, user, event_id)
        rows = [
            [
                report.collector_id,
                report.collector_name,
                report.transactions,
                report.cash,
                report.online,
                report.total,
                report.pending,
                report.mismatch,
            ]
        ]
        result = await self.exports.build(
            export_format,
            f"collector-report-{collector_id}",
            ["Collector ID", "Collector", "Transactions", "Cash", "Online", "Total", "Pending", "Mismatch"],
            rows,
        )
        event = await self._export_event(event_id, user)
        await self._audit_export(user, context, "collector", export_format, event["_id"] if event else None)
        return result

    async def export_guests(
        self,
        event_id: str | None,
        export_format: ExportFormat,
        user: dict[str, Any],
        context: dict[str, str | None],
    ) -> ExportFile:
        items, total = await self.guest_report(user, event_id, 1, self.MAX_EXPORT_ROWS)
        self._validate_export_size(total)
        rows = [
            [
                item.guest_id,
                item.full_name,
                item.family_name,
                item.relationship,
                item.contribution,
                item.gift_items,
                item.gift_estimated_value,
            ]
            for item in items
        ]
        result = await self.exports.build(
            export_format,
            f"guest-report-{event_id or 'all'}",
            [
                "Guest ID",
                "Guest",
                "Family",
                "Relationship",
                "Contribution",
                "Gift Items",
                "Gift Estimated Value",
            ],
            rows,
        )
        event = await self._export_event(event_id, user)
        await self._audit_export(user, context, "guest", export_format, event["_id"] if event else None)
        return result

    async def export_reconciliations(
        self,
        event_id: str | None,
        export_format: ExportFormat,
        user: dict[str, Any],
        context: dict[str, str | None],
    ) -> ExportFile:
        items, total = await self.reconciliation_report(user, event_id, 1, self.MAX_EXPORT_ROWS)
        self._validate_export_size(total)
        rows = [
            [
                item.reconciliation_id,
                item.event_id,
                item.collector_id,
                item.collector_name,
                item.expected_cash,
                item.actual_cash,
                item.difference,
                item.status,
                item.submitted_at,
            ]
            for item in items
        ]
        result = await self.exports.build(
            export_format,
            f"reconciliation-report-{event_id or 'all'}",
            [
                "Reconciliation ID",
                "Event ID",
                "Collector ID",
                "Collector",
                "Expected Cash",
                "Actual Cash",
                "Difference",
                "Status",
                "Submitted At",
            ],
            rows,
        )
        event = await self._export_event(event_id, user)
        await self._audit_export(
            user, context, "reconciliation", export_format, event["_id"] if event else None
        )
        return result

    async def _event_scope(self, user: dict[str, Any], event_id: str | None) -> list[Any] | None:
        if event_id:
            event = await self.access.event_for_user(event_id, user)
            return [event["_id"]]
        return await self.access.allowed_event_ids(user)

    async def _export_event(self, event_id: str | None, user: dict[str, Any]) -> dict[str, Any] | None:
        return await self.access.event_for_user(event_id, user) if event_id else None

    async def _audit_export(
        self,
        user: dict[str, Any],
        context: dict[str, str | None],
        report_type: str,
        export_format: ExportFormat,
        event_id: Any,
    ) -> None:
        await self.audit.record(
            user_id=user["_id"],
            action="EXPORT",
            request_id=context.get("request_id"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            event_id=event_id,
            entity_type="report",
            entity_id=user["_id"],
            new_value={"report_type": report_type, "format": export_format.value},
        )

    @staticmethod
    def _validate_dates(start_at: datetime | None, end_at: datetime | None) -> None:
        if start_at is not None and end_at is not None and start_at > end_at:
            raise AppError("VALIDATION_ERROR", "start_at must not be after end_at", 422)

    def _validate_export_size(self, total: int) -> None:
        if total > self.MAX_EXPORT_ROWS:
            raise AppError(
                "EXPORT_LIMIT_EXCEEDED",
                f"Exports are limited to {self.MAX_EXPORT_ROWS} rows",
                422,
            )

    @staticmethod
    def _amount(value: Decimal128 | Decimal | None) -> Decimal:
        return Decimal("0.00") if value is None else from_decimal128(value)

    def _dashboard_from_raw(self, raw: dict[str, Any]) -> DashboardData:
        transactions = raw.get("transactions", {})
        totals = transactions.get("totals", [])
        total = totals[0] if totals else {}
        gifts = raw.get("gifts", {})
        gift_totals = gifts.get("totals", [])
        gift_total = gift_totals[0] if gift_totals else {}
        return DashboardData(
            total_guests=int(raw.get("total_guests", 0)),
            total_contributions=self._amount(total.get("total_contributions")),
            total_cash=self._amount(total.get("total_cash")),
            total_online=self._amount(total.get("total_online")),
            total_gift_items=int(gift_total.get("quantity", 0)),
            verified_amount=self._amount(total.get("verified_amount")),
            pending_amount=self._amount(total.get("pending_amount")),
            collectors=int(raw.get("collectors", 0)),
            unreconciled_amount=self._amount(raw.get("unreconciled_amount")),
            contributions_over_time=[
                AmountPoint(label=item["_id"], amount=self._amount(item.get("amount")))
                for item in transactions.get("contributions_over_time", [])
            ],
            cash_vs_online=[
                AmountPoint(label=item["_id"], amount=self._amount(item.get("amount")))
                for item in transactions.get("cash_vs_online", [])
            ],
            collector_wise_collection=[
                CollectorAmountPoint(
                    collector_id=item.get("collector_id") or "Unknown",
                    collector_name=item["collector_name"],
                    transactions=int(item["transactions"]),
                    amount=self._amount(item.get("amount")),
                )
                for item in transactions.get("collector_wise_collection", [])
            ],
            transaction_status=[
                TransactionStatusPoint(
                    status=item["_id"],
                    transactions=int(item["transactions"]),
                    amount=self._amount(item.get("amount")),
                )
                for item in transactions.get("transaction_status", [])
            ],
            gift_categories=[
                GiftCategoryPoint(gift_type=item["_id"], quantity=int(item["quantity"]))
                for item in gifts.get("categories", [])
            ],
            hourly_collection=[
                HourlyAmountPoint(hour=int(item["_id"]), amount=self._amount(item.get("amount")))
                for item in transactions.get("hourly_collection", [])
            ],
        )

    def _guest_item(self, item: dict[str, Any]) -> GuestReportItem:
        return GuestReportItem(
            guest_id=item["guest_id"],
            full_name=item["full_name"],
            family_name=item.get("family_name", ""),
            relationship=item.get("relationship", ""),
            contribution=self._amount(item.get("contribution")),
            gift_items=int(item.get("gift_items", 0)),
            gift_estimated_value=self._amount(item.get("gift_estimated_value")),
        )

    def _reconciliation_item(self, item: dict[str, Any]) -> ReconciliationReportItem:
        return ReconciliationReportItem(
            reconciliation_id=item["reconciliation_id"],
            event_id=item["event_public_id"],
            collector_id=item["collector_public_id"],
            collector_name=item["collector_name"],
            expected_cash=self._amount(item.get("expected_cash")),
            actual_cash=self._amount(item.get("actual_cash")),
            difference=self._amount(item.get("difference")),
            status=item["status"],
            submitted_at=item["submitted_at"],
            verified_at=item.get("verified_at"),
            resolved_at=item.get("resolved_at"),
        )
