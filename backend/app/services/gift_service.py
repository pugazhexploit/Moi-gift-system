"""Event-scoped physical gift workflow with collector ownership checks."""

from __future__ import annotations

from typing import Any

from bson import ObjectId

from app.core.exceptions import AppError
from app.core.security import utc_now
from app.models.user import UserRole
from app.repositories.collectors import CollectorRepository
from app.repositories.counters import CounterRepository
from app.repositories.gifts import GiftRepository
from app.repositories.guests import GuestRepository
from app.schemas.gift import GiftCreate, GiftResponse, GiftUpdate
from app.services.audit_service import AuditService
from app.services.event_access_service import EventAccessService
from app.utils.money import to_decimal128


class GiftService:
    def __init__(self, database: Any) -> None:
        self.gifts = GiftRepository(database)
        self.guests = GuestRepository(database)
        self.collectors = CollectorRepository(database)
        self.counters = CounterRepository(database)
        self.access = EventAccessService(database)
        self.audit = AuditService(database)

    async def create(
        self, payload: GiftCreate, user: dict[str, Any], context: dict[str, str | None]
    ) -> GiftResponse:
        if UserRole(user["role"]) is UserRole.VIEWER:
            raise AppError("FORBIDDEN", "You are not allowed to record gifts", 403)
        event = await self.access.event_for_user(payload.event_id, user)
        guest = await self.guests.get_by_public_id(payload.guest_id)
        if guest is None or guest["event_id"] != event["_id"]:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        collector = await self._resolve_collector(payload.collector_id, event["_id"], user)
        now = utc_now()
        gift = await self.gifts.create(
            {
                "gift_id": await self.counters.next_id("GFT"),
                "event_id": event["_id"],
                "event_public_id": event["event_id"],
                "guest_id": guest["_id"],
                "guest_public_id": guest["guest_id"],
                "collector_id": collector["_id"],
                "collector_public_id": collector["collector_id"],
                "gift_type": payload.gift_type,
                "description": payload.description,
                "quantity": payload.quantity,
                "estimated_value": to_decimal128(payload.estimated_value)
                if payload.estimated_value is not None
                else None,
                "currency": payload.currency,
                "notes": payload.notes,
                "status": "received",
                "created_at": now,
                "updated_at": now,
            }
        )
        await self.audit.record(
            user_id=user["_id"],
            action="CREATE",
            request_id=context.get("request_id"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            event_id=event["_id"],
            entity_type="gift",
            entity_id=gift["_id"],
            new_value={"gift_id": gift["gift_id"], "status": gift["status"]},
        )
        return self.to_response(gift)

    async def get(self, gift_id: str, user: dict[str, Any]) -> GiftResponse:
        return self.to_response(await self._gift_for_user(gift_id, user))

    async def list(
        self, user: dict[str, Any], page: int, limit: int, event_id: str | None
    ) -> tuple[list[GiftResponse], int]:
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
        gifts, total = await self.gifts.list(query, page, limit)
        return [self.to_response(gift) for gift in gifts], total

    async def update(
        self,
        gift_id: str,
        payload: GiftUpdate,
        user: dict[str, Any],
        context: dict[str, str | None],
    ) -> GiftResponse:
        if UserRole(user["role"]) is UserRole.VIEWER:
            raise AppError("FORBIDDEN", "You are not allowed to update gifts", 403)
        gift = await self._gift_for_user(gift_id, user)
        changes = payload.model_dump(exclude_unset=True)
        if "estimated_value" in changes and changes["estimated_value"] is not None:
            changes["estimated_value"] = to_decimal128(changes["estimated_value"])
        updated = await self.gifts.update(gift_id, changes, utc_now())
        if updated is None:
            raise AppError("GIFT_FINALIZED", "Cancelled gifts cannot be modified", 409)
        await self.audit.record(
            user_id=user["_id"],
            action="UPDATE",
            request_id=context.get("request_id"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            event_id=gift["event_id"],
            entity_type="gift",
            entity_id=gift["_id"],
            old_value={"fields": sorted(changes)},
            new_value={"gift_id": gift_id, "status": updated["status"]},
        )
        return self.to_response(updated)

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
        else:
            if not supplied_collector_id:
                raise AppError("VALIDATION_ERROR", "collector_id is required for administrator entry", 422)
            collector = await self.collectors.get_by_public_id(supplied_collector_id)
            if collector is None:
                raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        if collector.get("status") != "active" or not await self.collectors.is_assigned(
            event_object_id, collector["_id"]
        ):
            raise AppError("FORBIDDEN", "Collector is not assigned to this event", 403)
        return collector

    async def _gift_for_user(self, gift_id: str, user: dict[str, Any]) -> dict[str, Any]:
        gift = await self.gifts.get_by_public_id(gift_id)
        if gift is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        await self.access.event_for_user(gift["event_public_id"], user)
        if UserRole(user["role"]) is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            if collector is None or collector["_id"] != gift["collector_id"]:
                raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        return gift

    @staticmethod
    def to_response(gift: dict[str, Any]) -> GiftResponse:
        from app.utils.money import from_decimal128

        return GiftResponse(
            gift_id=gift["gift_id"],
            event_id=gift["event_public_id"],
            guest_id=gift["guest_public_id"],
            collector_id=gift["collector_public_id"],
            gift_type=gift["gift_type"],
            description=gift["description"],
            quantity=gift["quantity"],
            estimated_value=from_decimal128(gift["estimated_value"])
            if gift.get("estimated_value") is not None
            else None,
            currency=gift["currency"],
            notes=gift.get("notes", ""),
            status=gift["status"],
            created_at=gift["created_at"],
            updated_at=gift["updated_at"],
        )
