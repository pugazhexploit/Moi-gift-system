"""Async MongoDB lifecycle, schema validation, and deliberate indexes."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient, IndexModel
from pymongo.errors import CollectionInvalid, OperationFailure, PyMongoError
from pymongo.server_api import ServerApi

from app.core.config import Settings


logger = logging.getLogger("giftledger")


CRITICAL_VALIDATORS: dict[str, dict[str, Any]] = {
    "users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["username", "email", "password_hash", "role", "status", "created_at", "updated_at"],
            "properties": {
                "username": {"bsonType": "string"}, "email": {"bsonType": "string"},
                "password_hash": {"bsonType": "string"}, "role": {"enum": ["admin", "collector", "viewer"]},
                "status": {"enum": ["active", "disabled"]}, "created_at": {"bsonType": "date"}, "updated_at": {"bsonType": "date"},
            },
        }
    },
    "events": {
        "$jsonSchema": {
            "bsonType": "object", "required": ["event_id", "event_name", "event_type", "event_date", "status", "created_at", "updated_at"],
            "properties": {"event_id": {"bsonType": "string"}, "event_name": {"bsonType": "string"}, "event_type": {"bsonType": "string"}, "event_date": {"bsonType": "date"}, "status": {"enum": ["draft", "active", "completed", "archived"]}},
        }
    },
    "guests": {
        "$jsonSchema": {
            "bsonType": "object", "required": ["guest_id", "event_id", "full_name", "created_at", "updated_at"],
            "properties": {"guest_id": {"bsonType": "string"}, "event_id": {"bsonType": "objectId"}, "full_name": {"bsonType": "string"}},
        }
    },
    "transactions": {
        "$jsonSchema": {
            "bsonType": "object", "required": ["transaction_id", "event_id", "guest_id", "collector_id", "amount", "currency", "payment_method", "transaction_type", "status", "created_at", "updated_at"],
            "properties": {"transaction_id": {"bsonType": "string"}, "event_id": {"bsonType": "objectId"}, "guest_id": {"bsonType": "objectId"}, "collector_id": {"bsonType": "objectId"}, "amount": {"bsonType": "decimal"}, "currency": {"bsonType": "string"}, "payment_method": {"enum": ["cash", "upi", "bank_transfer", "cheque", "other"]}, "status": {"enum": ["pending", "verified", "rejected", "cancelled", "locked"]}},
        }
    },
    "gifts": {"$jsonSchema": {"bsonType": "object", "required": ["gift_id", "event_id", "guest_id", "collector_id", "gift_type", "quantity", "currency", "status", "created_at"], "properties": {"gift_id": {"bsonType": "string"}, "event_id": {"bsonType": "objectId"}, "quantity": {"bsonType": ["int", "long"], "minimum": 1}, "estimated_value": {"bsonType": ["decimal", "null"]}}}},
    "reconciliations": {"$jsonSchema": {"bsonType": "object", "required": ["reconciliation_id", "event_id", "collector_id", "expected_cash", "actual_cash", "difference", "status", "submitted_by", "submitted_at"], "properties": {"reconciliation_id": {"bsonType": "string"}, "event_id": {"bsonType": "objectId"}, "collector_id": {"bsonType": "objectId"}, "expected_cash": {"bsonType": "decimal"}, "actual_cash": {"bsonType": "decimal"}, "difference": {"bsonType": "decimal"}, "status": {"enum": ["pending", "submitted", "verified", "mismatch", "resolved"]}}}},
}


INDEXES: Mapping[str, list[IndexModel]] = {
    "users": [IndexModel([("email", ASCENDING)], unique=True), IndexModel([("username", ASCENDING)], unique=True), IndexModel([("email_normalized", ASCENDING)], unique=True), IndexModel([("username_normalized", ASCENDING)], unique=True)],
    "events": [IndexModel([("event_id", ASCENDING)], unique=True), IndexModel([("event_date", DESCENDING), ("status", ASCENDING)])],
    "guests": [IndexModel([("guest_id", ASCENDING)], unique=True), IndexModel([("qr_token", ASCENDING)], unique=True), IndexModel([("event_id", ASCENDING), ("normalized_name", ASCENDING)]), IndexModel([("event_id", ASCENDING), ("normalized_phone", ASCENDING)]), IndexModel([("event_id", ASCENDING), ("normalized_name", ASCENDING), ("normalized_family_name", ASCENDING)])],
    "collectors": [IndexModel([("collector_id", ASCENDING)], unique=True), IndexModel([("user_id", ASCENDING)], unique=True, sparse=True)],
    "event_collectors": [IndexModel([("event_id", ASCENDING), ("collector_id", ASCENDING)], unique=True), IndexModel([("collector_id", ASCENDING), ("status", ASCENDING)])],
    "transactions": [IndexModel([("transaction_id", ASCENDING)], unique=True), IndexModel([("event_id", ASCENDING), ("idempotency_key", ASCENDING)], unique=True, partialFilterExpression={"idempotency_key": {"$type": "string"}}), IndexModel([("event_id", ASCENDING), ("created_at", DESCENDING)]), IndexModel([("event_id", ASCENDING), ("payment_method", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)]), IndexModel([("guest_id", ASCENDING), ("created_at", DESCENDING)]), IndexModel([("collector_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)]), IndexModel([("event_id", ASCENDING), ("reference_number", ASCENDING)], unique=True, partialFilterExpression={"reference_number": {"$type": "string"}})],
    "gifts": [IndexModel([("gift_id", ASCENDING)], unique=True), IndexModel([("event_id", ASCENDING), ("gift_type", ASCENDING), ("created_at", DESCENDING)]), IndexModel([("event_id", ASCENDING), ("guest_id", ASCENDING), ("created_at", DESCENDING)])],
    "receipts": [IndexModel([("receipt_id", ASCENDING)], unique=True), IndexModel([("transaction_id", ASCENDING)], unique=True), IndexModel([("verification_token_hash", ASCENDING)], unique=True)],
    "reconciliations": [IndexModel([("reconciliation_id", ASCENDING)], unique=True), IndexModel([("event_id", ASCENDING), ("status", ASCENDING), ("submitted_at", DESCENDING)]), IndexModel([("event_id", ASCENDING), ("collector_id", ASCENDING), ("submitted_at", DESCENDING)]), IndexModel([("collector_id", ASCENDING), ("status", ASCENDING), ("submitted_at", DESCENDING)])],
    "audit_logs": [IndexModel([("timestamp", DESCENDING)]), IndexModel([("user_id", ASCENDING), ("timestamp", DESCENDING)]), IndexModel([("entity_id", ASCENDING), ("timestamp", DESCENDING)])],
    "refresh_tokens": [IndexModel([("token_hash", ASCENDING)], unique=True), IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0), IndexModel([("user_id", ASCENDING), ("revoked_at", ASCENDING)])],
    "schema_migrations": [IndexModel([("version", ASCENDING)], unique=True)],
    "counters": [],
}


class DatabaseManager:
    """Owns one asynchronous MongoDB client for the application process."""

    def __init__(self) -> None:
        self.client: AsyncMongoClient | None = None
        self.database_name: str | None = None
        self.timeout_ms: int = 3_000

    async def connect(self, settings: Settings) -> None:
        client_options: dict[str, Any] = {"serverSelectionTimeoutMS": settings.mongodb_server_selection_timeout_ms, "tz_aware": True}
        if "mongodb+srv" in settings.mongodb_uri or "ssl=true" in settings.mongodb_uri.lower() or "tls=true" in settings.mongodb_uri.lower():
            try:
                import certifi
                client_options["tlsCAFile"] = certifi.where()
            except ImportError:
                pass
        if settings.mongodb_server_api_version:
            client_options["server_api"] = ServerApi(settings.mongodb_server_api_version, strict=settings.mongodb_server_api_strict, deprecation_errors=settings.mongodb_server_api_deprecation_errors)
        self.client = AsyncMongoClient(settings.mongodb_uri, **client_options)
        self.database_name = settings.mongodb_database
        self.timeout_ms = settings.mongodb_server_selection_timeout_ms
        logger.info("mongodb client configured", extra={"endpoint": "mongodb"})

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()
            self.client = None

    @property
    def db(self) -> Any:
        if self.client is None or self.database_name is None:
            raise RuntimeError("Database client is not initialized")
        return self.client[self.database_name]

    def __getitem__(self, name: str) -> Any:
        return self.db[name]

    async def health(self) -> dict[str, str]:
        if self.client is None:
            return {"status": "unavailable", "detail": "Client is not initialized"}
        try:
            await asyncio.wait_for(self.client.admin.command("ping"), timeout=1.8)
            return {"status": "available"}
        except (TimeoutError, asyncio.TimeoutError):
            return {"status": "unavailable", "detail": "Database ping timed out (verify MongoDB Atlas IP whitelist)"}
        except PyMongoError as err:
            logger.warning("MongoDB health check ping failed: %s", err)
            return {"status": "unavailable", "detail": str(err)}

    async def initialize_database(self) -> None:
        """Create validation-enabled collections and idempotent indexes."""
        database = self.db
        for collection_name, validator in CRITICAL_VALIDATORS.items():
            try:
                await database.create_collection(collection_name, validator=validator, validationLevel="strict", validationAction="error")
            except CollectionInvalid:
                await database.command({"collMod": collection_name, "validator": validator, "validationLevel": "strict", "validationAction": "error"})
        for collection_name in INDEXES:
            if collection_name not in CRITICAL_VALIDATORS:
                try:
                    await database.create_collection(collection_name)
                except CollectionInvalid:
                    pass
            if INDEXES[collection_name]:
                try:
                    await database[collection_name].create_indexes(INDEXES[collection_name])
                except OperationFailure as err:
                    if err.code == 86:
                        await database[collection_name].drop_indexes()
                        await database[collection_name].create_indexes(INDEXES[collection_name])
                    else:
                        raise
        logger.info("mongodb schema and indexes initialized", extra={"endpoint": "mongodb"})


database_manager = DatabaseManager()
