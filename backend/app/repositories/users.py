"""Controlled MongoDB access for user identity documents."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument

from app.models.user import UserRole, UserStatus


class UserRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database["users"]

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        if not ObjectId.is_valid(user_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(user_id)})

    async def get_by_identifier(self, identifier: str) -> dict[str, Any] | None:
        normalized = identifier.casefold()
        return await self.collection.find_one({"$or": [{"email_normalized": normalized}, {"username_normalized": normalized}]})

    async def create_user(self, username: str, email: str, password_hash: str, role: UserRole, now: datetime, session: Any = None) -> dict[str, Any]:
        document = {
            "username": username,
            "username_normalized": username.casefold(),
            "email": email,
            "email_normalized": email.casefold(),
            "password_hash": password_hash,
            "role": role.value,
            "status": UserStatus.ACTIVE.value,
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login_at": None,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(document, session=session)
        document["_id"] = result.inserted_id
        return document

    async def increment_failed_login(self, user_id: ObjectId, now: datetime) -> int:
        document = await self.collection.find_one_and_update(
            {"_id": user_id},
            {"$inc": {"failed_login_attempts": 1}, "$set": {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        return int(document["failed_login_attempts"])

    async def lock_account(self, user_id: ObjectId, locked_until: datetime, now: datetime) -> None:
        await self.collection.update_one(
            {"_id": user_id},
            {"$max": {"locked_until": locked_until}, "$set": {"updated_at": now}},
        )

    async def record_successful_login(self, user_id: ObjectId, now: datetime, password_hash: str | None = None, session: Any = None) -> None:
        update: dict[str, Any] = {"failed_login_attempts": 0, "locked_until": None, "last_login_at": now, "updated_at": now}
        if password_hash is not None:
            update["password_hash"] = password_hash
        await self.collection.update_one({"_id": user_id}, {"$set": update}, session=session)

    async def change_password(self, user_id: ObjectId, password_hash: str, now: datetime, session: Any = None) -> None:
        await self.collection.update_one({"_id": user_id}, {"$set": {"password_hash": password_hash, "failed_login_attempts": 0, "locked_until": None, "updated_at": now}}, session=session)

    async def list_users(self, page: int, limit: int, role: str | None = None) -> tuple[list[dict[str, Any]], int]:
        query: dict[str, Any] = {}
        if role:
            query["role"] = role
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(limit)
        items = await cursor.to_list(length=limit)
        return items, total

    async def update_role(self, user_id: ObjectId, role: UserRole, now: datetime) -> dict[str, Any] | None:
        return await self.collection.find_one_and_update(
            {"_id": user_id},
            {"$set": {"role": role.value, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )

    async def update_status(self, user_id: ObjectId, status: UserStatus, now: datetime) -> dict[str, Any] | None:
        return await self.collection.find_one_and_update(
            {"_id": user_id},
            {"$set": {"status": status.value, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
