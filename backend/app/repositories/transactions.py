"""Transaction and receipt persistence with no raw client query support."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bson.decimal128 import Decimal128

from pymongo import ReturnDocument


class TransactionRepository:
    def __init__(self, database: Any) -> None:
        self.transactions = database["transactions"]
        self.receipts = database["receipts"]

    async def get_by_public_id(self, transaction_id: str) -> dict[str, Any] | None:
        return await self.transactions.find_one({"transaction_id": transaction_id})

    async def get_by_idempotency_key(self, event_id: Any, key: str) -> dict[str, Any] | None:
        return await self.transactions.find_one({"event_id": event_id, "idempotency_key": key})

    async def create(self, document: dict[str, Any], session: Any) -> dict[str, Any]:
        result = await self.transactions.insert_one(document, session=session)
        document["_id"] = result.inserted_id
        return document

    async def create_receipt(self, document: dict[str, Any], session: Any) -> dict[str, Any]:
        result = await self.receipts.insert_one(document, session=session)
        document["_id"] = result.inserted_id
        return document

    async def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        return await self.receipts.find_one({"receipt_id": receipt_id})

    async def get_receipt_by_transaction_id(self, transaction_id: Any) -> dict[str, Any] | None:
        return await self.receipts.find_one({"transaction_id": transaction_id})

    async def get_receipt_by_token_hash(self, token_hash: str) -> dict[str, Any] | None:
        return await self.receipts.find_one({"verification_token_hash": token_hash})

    async def list(self, query: dict[str, Any], page: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        total = await self.transactions.count_documents(query)
        cursor = self.transactions.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(limit)
        return [document async for document in cursor], total

    async def transition(self, transaction_id: str, expected_status: str, changes: dict[str, Any], now: datetime, session: Any) -> dict[str, Any] | None:
        return await self.transactions.find_one_and_update({"transaction_id": transaction_id, "status": expected_status}, {"$set": {**changes, "updated_at": now}}, return_document=ReturnDocument.AFTER, session=session)

    async def set_receipt_status(self, transaction_id: Any, verification_status: str, session: Any) -> None:
        await self.receipts.update_one({"transaction_id": transaction_id}, {"$set": {"verification_status": verification_status}}, session=session)

    async def expected_cash(
        self, event_id: Any, collector_id: Any, reconciled_through: datetime, session: Any
    ) -> Decimal128:
        cursor = self.transactions.aggregate(
            [
                {
                    "$match": {
                        "event_id": event_id,
                        "collector_id": collector_id,
                        "payment_method": "cash",
                        "status": {"$in": ["pending", "verified", "locked"]},
                        "created_at": {"$lte": reconciled_through},
                    }
                },
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
            ],
            session=session,
        )
        async for result in cursor:
            return result["total"]
        return Decimal128("0.00")
