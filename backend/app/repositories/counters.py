"""Atomic counters for GiftLedger human-readable IDs."""

from __future__ import annotations

from typing import Any

from pymongo import ReturnDocument

from app.utils.identifiers import format_sequence_id


class CounterRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database["counters"]

    async def next_id(self, prefix: str, session: Any = None) -> str:
        counter = await self.collection.find_one_and_update({"_id": prefix}, {"$inc": {"sequence": 1}}, upsert=True, return_document=ReturnDocument.AFTER, session=session)
        return format_sequence_id(prefix, int(counter["sequence"]))
