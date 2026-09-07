"""Refresh-token persistence. Only keyed hashes are stored."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument


class RefreshTokenRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database["refresh_tokens"]

    async def create(self, token_hash: str, user_id: ObjectId, family_id: str, issued_at: datetime, expires_at: datetime, session: Any = None) -> None:
        await self.collection.insert_one({"token_hash": token_hash, "user_id": user_id, "family_id": family_id, "issued_at": issued_at, "expires_at": expires_at, "revoked_at": None, "replaced_by_hash": None}, session=session)

    async def get(self, token_hash: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"token_hash": token_hash})

    async def consume(self, token_hash: str, now: datetime, replacement_hash: str, session: Any = None) -> dict[str, Any] | None:
        return await self.collection.find_one_and_update({"token_hash": token_hash, "revoked_at": None, "expires_at": {"$gt": now}}, {"$set": {"revoked_at": now, "replaced_by_hash": replacement_hash}}, return_document=ReturnDocument.BEFORE, session=session)

    async def revoke_family(self, family_id: str, now: datetime, session: Any = None) -> None:
        await self.collection.update_many({"family_id": family_id, "revoked_at": None}, {"$set": {"revoked_at": now}}, session=session)

    async def revoke_user_tokens(self, user_id: ObjectId, now: datetime, session: Any = None) -> None:
        await self.collection.update_many({"user_id": user_id, "revoked_at": None}, {"$set": {"revoked_at": now}}, session=session)
