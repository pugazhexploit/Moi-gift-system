"""Central event-scope authorization used by every event-bound feature."""

from __future__ import annotations

from typing import Any

from app.core.exceptions import AppError
from app.models.user import UserRole
from app.repositories.collectors import CollectorRepository
from app.repositories.events import EventRepository


class EventAccessService:
    def __init__(self, database: Any) -> None:
        self.events = EventRepository(database)
        self.collectors = CollectorRepository(database)

    async def event_for_user(self, event_id: str, user: dict[str, Any]) -> dict[str, Any]:
        event = await self.events.get_by_public_id(event_id)
        if event is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        if await self.can_access_event(event, user):
            return event
        raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)

    async def can_access_event(self, event: dict[str, Any], user: dict[str, Any]) -> bool:
        role = UserRole(user["role"])
        if role is UserRole.ADMIN:
            return True
        if role is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            return collector is not None and await self.collectors.is_assigned(event["_id"], collector["_id"])
        return user["_id"] in event.get("viewer_user_ids", [])

    async def allowed_event_ids(self, user: dict[str, Any]) -> list[Any] | None:
        role = UserRole(user["role"])
        if role is UserRole.ADMIN:
            return None
        if role is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            return [] if collector is None else await self.collectors.active_event_ids(collector["_id"])
        return await self.events.viewer_event_ids(user["_id"])
