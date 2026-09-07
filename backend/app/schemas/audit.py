"""Audit log query and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str | None = None
    event_id: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    old_value: dict[str, Any] = {}
    new_value: dict[str, Any] = {}
    ip_address: str = ""
    user_agent: str = ""
    request_id: str = ""
    timestamp: datetime
