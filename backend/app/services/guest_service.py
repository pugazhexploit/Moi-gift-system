"""Event-scoped guest management, duplicate detection, and QR lookups."""

from __future__ import annotations

from typing import Any

from app.core.exceptions import AppError
from app.core.security import utc_now
from app.models.user import UserRole
from app.repositories.counters import CounterRepository
from app.repositories.guests import GuestRepository
from app.schemas.guest import GuestCreate, GuestQrResponse, GuestResponse, GuestUpdate
from app.services.audit_service import AuditService
from app.services.event_access_service import EventAccessService
from app.utils.identifiers import generate_qr_token
from app.utils.normalization import normalize_phone, normalize_text


class GuestService:
    def __init__(self, database: Any) -> None:
        self.guests = GuestRepository(database)
        self.counters = CounterRepository(database)
        self.access = EventAccessService(database)
        self.audit = AuditService(database)

    async def create(self, payload: GuestCreate, user: dict[str, Any], context: dict[str, str | None]) -> GuestResponse:
        if UserRole(user["role"]) is UserRole.VIEWER:
            raise AppError("FORBIDDEN", "You are not allowed to create guests", 403)
        event = await self.access.event_for_user(payload.event_id, user)
        normalized_name = normalize_text(payload.full_name)
        normalized_phone = normalize_phone(payload.phone)
        normalized_family_name = normalize_text(payload.family_name) if payload.family_name else ""
        duplicate = await self.guests.find_duplicate(event["_id"], normalized_phone, normalized_name, normalized_family_name)
        if duplicate:
            raise AppError("DUPLICATE_GUEST", "A matching guest already exists for this event", 409)
        now = utc_now()
        document = payload.model_dump()
        document.pop("event_id")
        document.update({"guest_id": await self.counters.next_id("GST"), "event_id": event["_id"], "event_public_id": event["event_id"], "normalized_name": normalized_name, "normalized_phone": normalized_phone, "normalized_family_name": normalized_family_name, "qr_token": generate_qr_token(), "created_at": now, "updated_at": now})
        guest = await self.guests.create(document)
        await self.audit.record(user_id=user["_id"], action="CREATE", request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), event_id=event["_id"], entity_type="guest", entity_id=guest["_id"], new_value={"guest_id": guest["guest_id"]})
        return self.to_response(guest)

    async def get(self, guest_id: str, user: dict[str, Any]) -> GuestResponse:
        return self.to_response(await self._guest_for_user(guest_id, user))

    async def list(self, user: dict[str, Any], page: int, limit: int, search: str | None, event_id: str | None) -> tuple[list[GuestResponse], int]:
        allowed = await self.access.allowed_event_ids(user)
        query: dict[str, Any] = {} if allowed is None else {"event_id": {"$in": allowed}}
        if event_id:
            event = await self.access.event_for_user(event_id, user)
            query["event_id"] = event["_id"]
        guests, total = await self.guests.get_many(query, page, limit, search)
        return [self.to_response(guest) for guest in guests], total

    async def update(self, guest_id: str, payload: GuestUpdate, user: dict[str, Any], context: dict[str, str | None]) -> GuestResponse:
        if UserRole(user["role"]) is UserRole.VIEWER:
            raise AppError("FORBIDDEN", "You are not allowed to update guests", 403)
        guest = await self._guest_for_user(guest_id, user)
        changes = payload.model_dump(exclude_unset=True)
        merged = {**guest, **changes}
        if {"full_name", "phone", "family_name"}.intersection(changes):
            normalized_name = normalize_text(merged["full_name"])
            normalized_phone = normalize_phone(merged.get("phone"))
            normalized_family_name = normalize_text(merged["family_name"]) if merged.get("family_name") else ""
            duplicate = await self.guests.find_duplicate(guest["event_id"], normalized_phone, normalized_name, normalized_family_name)
            if duplicate and duplicate["_id"] != guest["_id"]:
                raise AppError("DUPLICATE_GUEST", "A matching guest already exists for this event", 409)
            changes.update({"normalized_name": normalized_name, "normalized_phone": normalized_phone, "normalized_family_name": normalized_family_name})
        updated = await self.guests.update(guest_id, changes, utc_now())
        assert updated is not None
        await self.audit.record(user_id=user["_id"], action="UPDATE", request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), event_id=guest["event_id"], entity_type="guest", entity_id=guest["_id"], old_value={"fields": sorted(changes)}, new_value={"guest_id": guest_id})
        return self.to_response(updated)

    async def qr_token(self, guest_id: str, user: dict[str, Any]) -> GuestQrResponse:
        if UserRole(user["role"]) is UserRole.VIEWER:
            raise AppError("FORBIDDEN", "You are not allowed to access guest QR codes", 403)
        guest = await self._guest_for_user(guest_id, user)
        return GuestQrResponse(guest_id=guest["guest_id"], qr_token=guest["qr_token"])

    async def scan(self, qr_token: str, user: dict[str, Any]) -> GuestResponse:
        guest = await self.guests.get_by_qr_token(qr_token)
        if guest is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        event = await self.access.events.get_by_public_id(guest["event_public_id"])
        if event is None or not await self.access.can_access_event(event, user):
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        return self.to_response(guest)

    async def _guest_for_user(self, guest_id: str, user: dict[str, Any]) -> dict[str, Any]:
        guest = await self.guests.get_by_public_id(guest_id)
        if guest is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        event = await self.access.events.get_by_public_id(guest["event_public_id"])
        if event is None or not await self.access.can_access_event(event, user):
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        return guest

    @staticmethod
    def to_response(guest: dict[str, Any]) -> GuestResponse:
        return GuestResponse(guest_id=guest["guest_id"], event_id=guest["event_public_id"], full_name=guest["full_name"], phone=guest.get("phone", ""), email=guest.get("email"), address=guest.get("address", {}), relationship=guest.get("relationship", ""), family_name=guest.get("family_name", ""), notes=guest.get("notes", ""), created_at=guest["created_at"], updated_at=guest["updated_at"])
