"""Event business logic and audit-safe projections."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from app.core.exceptions import AppError
from app.core.security import utc_now
from app.models.user import UserRole
from app.repositories.counters import CounterRepository
from app.repositories.events import EventRepository
from app.repositories.users import UserRepository
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.services.audit_service import AuditService
from app.services.event_access_service import EventAccessService


class EventService:
    def __init__(self, database: Any) -> None:
        self.events = EventRepository(database)
        self.counters = CounterRepository(database)
        self.users = UserRepository(database)
        self.audit = AuditService(database)
        self.access = EventAccessService(database)

    async def create(self, payload: EventCreate, user: dict[str, Any], context: dict[str, str | None]) -> EventResponse:
        now = utc_now()
        event = await self.events.create({"event_id": await self.counters.next_id("EVT"), **payload.model_dump(), "viewer_user_ids": [], "created_by": user["_id"], "created_at": now, "updated_at": now})
        await self.audit.record(user_id=user["_id"], action="CREATE", request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), event_id=event["_id"], entity_type="event", entity_id=event["_id"], new_value={"event_id": event["event_id"]})
        return self.to_response(event)

    async def get(self, event_id: str, user: dict[str, Any]) -> EventResponse:
        return self.to_response(await self.access.event_for_user(event_id, user))

    async def list(self, user: dict[str, Any], page: int, limit: int, search: str | None, status: str | None) -> tuple[list[EventResponse], int]:
        allowed = await self.access.allowed_event_ids(user)
        query: dict[str, Any] = {} if allowed is None else {"_id": {"$in": allowed}}
        if status:
            query["status"] = status
        events, total = await self.events.get_many(query, page, limit, search)
        return [self.to_response(event) for event in events], total

    async def update(self, event_id: str, payload: EventUpdate, user: dict[str, Any], context: dict[str, str | None]) -> EventResponse:
        event = await self.access.event_for_user(event_id, user)
        changes = payload.model_dump(exclude_unset=True)
        updated = await self.events.update(event_id, changes, utc_now())
        assert updated is not None
        await self.audit.record(user_id=user["_id"], action="UPDATE", request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), event_id=event["_id"], entity_type="event", entity_id=event["_id"], old_value={"fields": sorted(changes)}, new_value={"event_id": event_id})
        return self.to_response(updated)

    async def assign_viewer(self, event_id: str, viewer_user_id: str, user: dict[str, Any], context: dict[str, str | None]) -> EventResponse:
        if not ObjectId.is_valid(viewer_user_id):
            raise AppError("VALIDATION_ERROR", "Invalid viewer account", 422)
        event = await self.events.get_by_public_id(event_id)
        viewer = await self.users.get_by_id(viewer_user_id)
        if event is None or viewer is None or viewer.get("role") != UserRole.VIEWER.value:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        updated = await self.events.add_viewer(event_id, ObjectId(viewer_user_id), utc_now())
        assert updated is not None
        await self.audit.record(user_id=user["_id"], action="UPDATE", request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), event_id=event["_id"], entity_type="event_viewer", entity_id=event["_id"], new_value={"event_id": event_id})
        return self.to_response(updated)

    @staticmethod
    def to_response(event: dict[str, Any]) -> EventResponse:
        return EventResponse(
            event_id=str(event.get("event_id", "")),
            event_name=str(event.get("event_name", "")),
            event_type=event.get("event_type", "other"),
            description=str(event.get("description", "")),
            venue=str(event.get("venue", "")),
            event_date=event.get("event_date", utc_now()),
            start_time=str(event.get("start_time", "")),
            end_time=str(event.get("end_time", "")),
            status=event.get("status", "active"),
            created_at=event.get("created_at", utc_now()),
            updated_at=event.get("updated_at", utc_now()),
        )
