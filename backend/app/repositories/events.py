"""Constrained queries for GiftLedger event documents."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pymongo import ReturnDocument


class EventRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database["events"]

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def get_by_public_id(self, event_id: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"event_id": event_id})

    async def viewer_event_ids(self, user_id: Any) -> list[Any]:
        cursor = self.collection.find({"viewer_user_ids": user_id}, {"_id": 1})
        return [document["_id"] async for document in cursor]

    async def get_many(self, query: dict[str, Any], page: int, limit: int, search: str | None = None) -> tuple[list[dict[str, Any]], int]:
        if search:
            query["event_name"] = {"$regex": re.escape(search), "$options": "i"}
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).sort("event_date", -1).skip((page - 1) * limit).limit(limit)
        return [document async for document in cursor], total

    async def update(self, event_id: str, changes: dict[str, Any], now: datetime) -> dict[str, Any] | None:
        return await self.collection.find_one_and_update({"event_id": event_id}, {"$set": {**changes, "updated_at": now}}, return_document=ReturnDocument.AFTER)

    async def add_viewer(self, event_id: str, viewer_user_id: Any, now: datetime) -> dict[str, Any] | None:
        return await self.collection.find_one_and_update({"event_id": event_id}, {"$addToSet": {"viewer_user_ids": viewer_user_id}, "$set": {"updated_at": now}}, return_document=ReturnDocument.AFTER)
