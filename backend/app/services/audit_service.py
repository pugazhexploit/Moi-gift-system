"""Append-only audit writer and reader for administrative audit trails."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.schemas.audit import AuditLogResponse


class AuditService:
    def __init__(self, database: Any) -> None:
        self.collection = database["audit_logs"]

    async def record(
        self,
        *,
        user_id: Any,
        action: str,
        request_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
        event_id: Any = None,
        entity_type: str = "user",
        entity_id: Any = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        session: Any = None,
    ) -> None:
        await self.collection.insert_one(
            {
                "user_id": user_id,
                "event_id": event_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id or user_id,
                "old_value": old_value or {},
                "new_value": new_value or {},
                "ip_address": ip_address or "",
                "user_agent": (user_agent or "")[:512],
                "request_id": request_id or "",
                "timestamp": datetime.now(timezone.utc),
            },
            session=session,
        )

    async def list(
        self,
        page: int,
        limit: int,
        action: str | None = None,
        entity_type: str | None = None,
    ) -> tuple[list[AuditLogResponse], int]:
        query: dict[str, Any] = {}
        if action:
            query["action"] = action
        if entity_type:
            query["entity_type"] = entity_type

        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).sort("timestamp", -1).skip((page - 1) * limit).limit(limit)
        docs = await cursor.to_list(length=limit)

        items = []
        for doc in docs:
            items.append(
                AuditLogResponse(
                    id=str(doc["_id"]),
                    user_id=str(doc["user_id"]) if doc.get("user_id") else None,
                    event_id=str(doc["event_id"]) if doc.get("event_id") else None,
                    action=doc.get("action", ""),
                    entity_type=doc.get("entity_type", ""),
                    entity_id=str(doc["entity_id"]) if doc.get("entity_id") else None,
                    old_value=doc.get("old_value") or {},
                    new_value=doc.get("new_value") or {},
                    ip_address=doc.get("ip_address", ""),
                    user_agent=doc.get("user_agent", ""),
                    request_id=doc.get("request_id", ""),
                    timestamp=doc.get("timestamp", datetime.now(timezone.utc)),
                )
            )
        return items, total
