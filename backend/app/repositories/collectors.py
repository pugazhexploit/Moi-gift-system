"""GiftLedger collector profile and event assignment persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo import ReturnDocument


class CollectorRepository:
    def __init__(self, database: Any) -> None:
        self.collectors = database["collectors"]
        self.assignments = database["event_collectors"]

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self.collectors.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def get_by_public_id(self, collector_id: str) -> dict[str, Any] | None:
        return await self.collectors.find_one({"collector_id": collector_id})

    async def get_by_user_id(self, user_id: Any) -> dict[str, Any] | None:
        return await self.collectors.find_one({"user_id": user_id})

    async def list(self, page: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        total = await self.collectors.count_documents({})
        cursor = self.collectors.find({}).sort("created_at", -1).skip((page - 1) * limit).limit(limit)
        return [document async for document in cursor], total

    async def update(self, collector_id: str, changes: dict[str, Any], now: datetime) -> dict[str, Any] | None:
        return await self.collectors.find_one_and_update({"collector_id": collector_id}, {"$set": {**changes, "updated_at": now}}, return_document=ReturnDocument.AFTER)

    async def assign(self, event_id: Any, collector_id: Any, now: datetime) -> dict[str, Any]:
        document = {"event_id": event_id, "collector_id": collector_id, "assigned_at": now, "status": "active"}
        await self.assignments.insert_one(document)
        return document

    async def active_event_ids(self, collector_id: Any) -> list[Any]:
        cursor = self.assignments.find({"collector_id": collector_id, "status": "active"}, {"event_id": 1})
        return [item["event_id"] async for item in cursor]

    async def is_assigned(self, event_id: Any, collector_id: Any) -> bool:
        return await self.assignments.find_one({"event_id": event_id, "collector_id": collector_id, "status": "active"}) is not None
