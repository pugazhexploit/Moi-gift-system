"""Constrained GiftLedger guest queries with indexed duplicate detection."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pymongo import ReturnDocument


class GuestRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database["guests"]

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def get_by_public_id(self, guest_id: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"guest_id": guest_id})

    async def get_by_qr_token(self, qr_token: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"qr_token": qr_token})

    async def find_duplicate(self, event_object_id: Any, normalized_phone: str | None, normalized_name: str, normalized_family_name: str) -> dict[str, Any] | None:
        if normalized_phone:
            duplicate = await self.collection.find_one({"event_id": event_object_id, "normalized_phone": normalized_phone})
            if duplicate:
                return duplicate
        if normalized_family_name:
            return await self.collection.find_one({"event_id": event_object_id, "normalized_name": normalized_name, "normalized_family_name": normalized_family_name})
        return None

    async def get_many(self, query: dict[str, Any], page: int, limit: int, search: str | None = None) -> tuple[list[dict[str, Any]], int]:
        if search:
            expression = re.escape(search)
            query["$or"] = [{"full_name": {"$regex": expression, "$options": "i"}}, {"phone": {"$regex": expression, "$options": "i"}}, {"guest_id": {"$regex": expression, "$options": "i"}}, {"family_name": {"$regex": expression, "$options": "i"}}, {"relationship": {"$regex": expression, "$options": "i"}}]
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(limit)
        return [document async for document in cursor], total

    async def update(self, guest_id: str, changes: dict[str, Any], now: datetime) -> dict[str, Any] | None:
        return await self.collection.find_one_and_update({"guest_id": guest_id}, {"$set": {**changes, "updated_at": now}}, return_document=ReturnDocument.AFTER)
