"""Admin-controlled collector profiles and event assignments."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import AppError
from app.core.security import utc_now
from app.models.user import UserRole
from app.repositories.collectors import CollectorRepository
from app.repositories.counters import CounterRepository
from app.repositories.events import EventRepository
from app.repositories.users import UserRepository
from app.schemas.collector import AssignmentResponse, CollectorCreate, CollectorResponse, CollectorUpdate
from app.services.audit_service import AuditService


class CollectorService:
    def __init__(self, database: Any) -> None:
        self.collectors = CollectorRepository(database)
        self.events = EventRepository(database)
        self.users = UserRepository(database)
        self.counters = CounterRepository(database)
        self.audit = AuditService(database)

    async def create(self, payload: CollectorCreate, user: dict[str, Any], context: dict[str, str | None]) -> CollectorResponse:
        if not ObjectId.is_valid(payload.user_id):
            raise AppError("VALIDATION_ERROR", "Invalid collector user", 422)
        account = await self.users.get_by_id(payload.user_id)
        if account is None or account.get("role") != UserRole.COLLECTOR.value:
            raise AppError("VALIDATION_ERROR", "Collector account is invalid", 422)
        now = utc_now()
        document = payload.model_dump()
        document["user_id"] = ObjectId(payload.user_id)
        document["collector_id"] = await self.counters.next_id("COL")
        document["created_at"] = now
        document["updated_at"] = now
        try:
            collector = await self.collectors.create(document)
        except DuplicateKeyError as exc:
            raise AppError("COLLECTOR_EXISTS", "A profile already exists for this collector", 409) from exc
        await self.audit.record(user_id=user["_id"], action="CREATE", request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), entity_type="collector", entity_id=collector["_id"], new_value={"collector_id": collector["collector_id"]})
        return self.to_response(collector)

    async def list(self, page: int, limit: int) -> tuple[list[CollectorResponse], int]:
        collectors, total = await self.collectors.list(page, limit)
        return [self.to_response(collector) for collector in collectors], total

    async def update(self, collector_id: str, payload: CollectorUpdate, user: dict[str, Any], context: dict[str, str | None]) -> CollectorResponse:
        changes = payload.model_dump(exclude_unset=True)
        collector = await self.collectors.update(collector_id, changes, utc_now())
        if collector is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        await self.audit.record(user_id=user["_id"], action="UPDATE", request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), entity_type="collector", entity_id=collector["_id"], old_value={"fields": sorted(changes)}, new_value={"collector_id": collector_id})
        return self.to_response(collector)

    async def assign(self, event_id: str, collector_id: str, user: dict[str, Any], context: dict[str, str | None]) -> AssignmentResponse:
        event = await self.events.get_by_public_id(event_id)
        collector = await self.collectors.get_by_public_id(collector_id)
        if event is None or collector is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        now = utc_now()
        try:
            assignment = await self.collectors.assign(event["_id"], collector["_id"], now)
        except DuplicateKeyError as exc:
            raise AppError("ASSIGNMENT_EXISTS", "Collector is already assigned to this event", 409) from exc
        await self.audit.record(user_id=user["_id"], action="UPDATE", request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), event_id=event["_id"], entity_type="event_collector", entity_id=assignment["_id"], new_value={"collector_id": collector_id, "event_id": event_id})
        return AssignmentResponse(event_id=event_id, collector_id=collector_id, assigned_at=assignment["assigned_at"], status=assignment["status"])

    @staticmethod
    def to_response(collector: dict[str, Any]) -> CollectorResponse:
        return CollectorResponse(
            collector_id=str(collector.get("collector_id", "")),
            name=str(collector.get("name", "")),
            phone=str(collector.get("phone", "")),
            employee_code=collector.get("employee_code"),
            status=collector.get("status", "active"),
            created_at=collector.get("created_at", utc_now()),
            updated_at=collector.get("updated_at", utc_now()),
        )
