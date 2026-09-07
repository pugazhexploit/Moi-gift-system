"""Constrained persistence operations for physical gifts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo import ReturnDocument


class GiftRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database["gifts"]

    async def create(self, document: dict[str, Any], session: Any = None) -> dict[str, Any]:
        result = await self.collection.insert_one(document, session=session)
        document["_id"] = result.inserted_id
        return document

    async def get_by_public_id(self, gift_id: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"gift_id": gift_id})

    async def list(self, query: dict[str, Any], page: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(limit)
        return [gift async for gift in cursor], total

    async def update(
        self, gift_id: str, changes: dict[str, Any], now: datetime, session: Any = None
    ) -> dict[str, Any] | None:
        return await self.collection.find_one_and_update(
            {"gift_id": gift_id, "status": {"$ne": "cancelled"}},
            {"$set": {**changes, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
