"""Constrained persistence operations for collector cash reconciliations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo import ReturnDocument


class ReconciliationRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database["reconciliations"]

    async def create(self, document: dict[str, Any], session: Any) -> dict[str, Any]:
        result = await self.collection.insert_one(document, session=session)
        document["_id"] = result.inserted_id
        return document

    async def get_by_public_id(self, reconciliation_id: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"reconciliation_id": reconciliation_id})

    async def list(
        self, query: dict[str, Any], page: int, limit: int
    ) -> tuple[list[dict[str, Any]], int]:
        total = await self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort("submitted_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        return [document async for document in cursor], total

    async def transition(
        self,
        reconciliation_id: str,
        expected_status: str,
        changes: dict[str, Any],
        session: Any,
    ) -> dict[str, Any] | None:
        return await self.collection.find_one_and_update(
            {"reconciliation_id": reconciliation_id, "status": expected_status},
            {"$set": changes},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
