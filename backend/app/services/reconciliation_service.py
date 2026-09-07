"""Collector cash reconciliation with authoritative transaction totals."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.errors import OperationFailure, PyMongoError

from app.core.exceptions import AppError
from app.core.security import utc_now
from app.models.user import UserRole
from app.repositories.collectors import CollectorRepository
from app.repositories.counters import CounterRepository
from app.repositories.reconciliations import ReconciliationRepository
from app.repositories.transactions import TransactionRepository
from app.schemas.reconciliation import (
    ReconciliationAction,
    ReconciliationCreate,
    ReconciliationResponse,
    ReconciliationStatus,
)
from app.services.audit_service import AuditService
from app.services.event_access_service import EventAccessService
from app.utils.money import from_decimal128, normalize_money, to_decimal128


class ReconciliationService:
    def __init__(self, database: Any) -> None:
        self.database = database
        self.collectors = CollectorRepository(database)
        self.counters = CounterRepository(database)
        self.reconciliations = ReconciliationRepository(database)
        self.transactions = TransactionRepository(database)
        self.access = EventAccessService(database)
        self.audit = AuditService(database)

    async def create(
        self,
        payload: ReconciliationCreate,
        user: dict[str, Any],
        context: dict[str, str | None],
    ) -> ReconciliationResponse:
        event = await self.access.event_for_user(payload.event_id, user)
        collector = await self._resolve_collector(payload.collector_id, event["_id"], user)
        submitted_at = utc_now()

        async def create_reconciliation(session: Any) -> dict[str, Any]:
            expected_cash = from_decimal128(
                await self.transactions.expected_cash(event["_id"], collector["_id"], submitted_at, session)
            )
            actual_cash = normalize_money(payload.actual_cash)
            difference = normalize_money(actual_cash - expected_cash)
            if difference != 0 and not payload.reason:
                raise AppError(
                    "MISMATCH_REASON_REQUIRED",
                    "An explanation is required when actual cash does not match expected cash",
                    422,
                )
            status = (
                ReconciliationStatus.SUBMITTED.value
                if difference == 0
                else ReconciliationStatus.MISMATCH.value
            )
            reconciliation = await self.reconciliations.create(
                {
                    "reconciliation_id": await self.counters.next_id("REC", session=session),
                    "event_id": event["_id"],
                    "event_public_id": event["event_id"],
                    "collector_id": collector["_id"],
                    "collector_public_id": collector["collector_id"],
                    "expected_cash": to_decimal128(expected_cash),
                    "actual_cash": to_decimal128(actual_cash),
                    "difference": to_decimal128(difference),
                    "reason": payload.reason,
                    "status": status,
                    "submitted_by": user["_id"],
                    "submitted_at": submitted_at,
                    "reconciled_through": submitted_at,
                    "verified_by": None,
                    "verified_at": None,
                    "resolved_by": None,
                    "resolved_at": None,
                    "resolution_note": None,
                },
                session,
            )
            await self.audit.record(
                user_id=user["_id"],
                action="RECONCILE",
                request_id=context.get("request_id"),
                ip_address=context.get("ip_address"),
                user_agent=context.get("user_agent"),
                event_id=event["_id"],
                entity_type="reconciliation",
                entity_id=reconciliation["_id"],
                new_value={
                    "reconciliation_id": reconciliation["reconciliation_id"],
                    "status": status,
                    "difference": str(difference),
                },
                session=session,
            )
            return reconciliation

        return self.to_response(await self._with_transaction(create_reconciliation))

    async def get(self, reconciliation_id: str, user: dict[str, Any]) -> ReconciliationResponse:
        return self.to_response(await self._reconciliation_for_user(reconciliation_id, user))

    async def list(
        self,
        user: dict[str, Any],
        page: int,
        limit: int,
        event_id: str | None,
        status: ReconciliationStatus | None,
    ) -> tuple[list[ReconciliationResponse], int]:
        allowed = await self.access.allowed_event_ids(user)
        query: dict[str, Any] = {} if allowed is None else {"event_id": {"$in": allowed}}
        if event_id:
            event = await self.access.event_for_user(event_id, user)
            query["event_id"] = event["_id"]
        if UserRole(user["role"]) is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            if collector is None:
                return [], 0
            query["collector_id"] = collector["_id"]
        if status:
            query["status"] = status.value
        reconciliations, total = await self.reconciliations.list(query, page, limit)
        return [self.to_response(item) for item in reconciliations], total

    async def verify(
        self,
        reconciliation_id: str,
        user: dict[str, Any],
        context: dict[str, str | None],
    ) -> ReconciliationResponse:
        return await self._transition(
            reconciliation_id,
            ReconciliationStatus.SUBMITTED,
            {
                "status": ReconciliationStatus.VERIFIED.value,
                "verified_by": user["_id"],
                "verified_at": utc_now(),
            },
            "VERIFY",
            user,
            context,
        )

    async def resolve(
        self,
        reconciliation_id: str,
        action: ReconciliationAction,
        user: dict[str, Any],
        context: dict[str, str | None],
    ) -> ReconciliationResponse:
        if not action.reason:
            raise AppError("VALIDATION_ERROR", "A resolution note is required", 422)
        resolved_at = utc_now()
        return await self._transition(
            reconciliation_id,
            ReconciliationStatus.MISMATCH,
            {
                "status": ReconciliationStatus.RESOLVED.value,
                "verified_by": user["_id"],
                "verified_at": resolved_at,
                "resolved_by": user["_id"],
                "resolved_at": resolved_at,
                "resolution_note": action.reason,
            },
            "RECONCILE",
            user,
            context,
        )

    async def _resolve_collector(
        self, supplied_collector_id: str | None, event_object_id: ObjectId, user: dict[str, Any]
    ) -> dict[str, Any]:
        role = UserRole(user["role"])
        if role is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            if collector is None or (
                supplied_collector_id and supplied_collector_id != collector["collector_id"]
            ):
                raise AppError("FORBIDDEN", "You are not allowed to use this collector", 403)
        elif role is UserRole.ADMIN:
            if not supplied_collector_id:
                raise AppError("VALIDATION_ERROR", "collector_id is required for administrator entry", 422)
            collector = await self.collectors.get_by_public_id(supplied_collector_id)
            if collector is None:
                raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        else:
            raise AppError("FORBIDDEN", "You are not allowed to submit reconciliations", 403)
        if collector.get("status") != "active" or not await self.collectors.is_assigned(
            event_object_id, collector["_id"]
        ):
            raise AppError("FORBIDDEN", "Collector is not assigned to this event", 403)
        return collector

    async def _reconciliation_for_user(
        self, reconciliation_id: str, user: dict[str, Any]
    ) -> dict[str, Any]:
        reconciliation = await self.reconciliations.get_by_public_id(reconciliation_id)
        if reconciliation is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        await self.access.event_for_user(reconciliation["event_public_id"], user)
        if UserRole(user["role"]) is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            if collector is None or collector["_id"] != reconciliation["collector_id"]:
                raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        return reconciliation

    async def _transition(
        self,
        reconciliation_id: str,
        expected_status: ReconciliationStatus,
        changes: dict[str, Any],
        audit_action: str,
        user: dict[str, Any],
        context: dict[str, str | None],
    ) -> ReconciliationResponse:
        reconciliation = await self.reconciliations.get_by_public_id(reconciliation_id)
        if reconciliation is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)

        async def transition(session: Any) -> dict[str, Any] | None:
            updated = await self.reconciliations.transition(
                reconciliation_id, expected_status.value, changes, session
            )
            if updated is None:
                return None
            await self.audit.record(
                user_id=user["_id"],
                action=audit_action,
                request_id=context.get("request_id"),
                ip_address=context.get("ip_address"),
                user_agent=context.get("user_agent"),
                event_id=updated["event_id"],
                entity_type="reconciliation",
                entity_id=updated["_id"],
                old_value={"status": expected_status.value},
                new_value={
                    "reconciliation_id": reconciliation_id,
                    "status": updated["status"],
                },
                session=session,
            )
            return updated

        updated = await self._with_transaction(transition)
        if updated is None:
            raise AppError("INVALID_STATE", f"Reconciliation is not {expected_status.value}", 409)
        return self.to_response(updated)

    async def _with_transaction(self, callback: Any) -> Any:
        session = self.database.client.start_session()
        if hasattr(session, "__await__") and not hasattr(session, "__aenter__"):
            session = await session
        async with session as s:
            return await s.with_transaction(callback)

    @staticmethod
    def to_response(reconciliation: dict[str, Any]) -> ReconciliationResponse:
        return ReconciliationResponse(
            reconciliation_id=reconciliation["reconciliation_id"],
            event_id=reconciliation["event_public_id"],
            collector_id=reconciliation["collector_public_id"],
            expected_cash=from_decimal128(reconciliation["expected_cash"]),
            actual_cash=from_decimal128(reconciliation["actual_cash"]),
            difference=from_decimal128(reconciliation["difference"]),
            reason=reconciliation.get("reason", ""),
            status=reconciliation["status"],
            submitted_at=reconciliation["submitted_at"],
            verified_at=reconciliation.get("verified_at"),
            resolved_at=reconciliation.get("resolved_at"),
            resolution_note=reconciliation.get("resolution_note"),
        )
