"""Event request and response schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventType(StrEnum):
    WEDDING = "wedding"
    RECEPTION = "reception"
    BIRTHDAY = "birthday"
    FESTIVAL = "festival"
    TEMPLE_EVENT = "temple_event"
    FAMILY_FUNCTION = "family_function"
    COMMUNITY_EVENT = "community_event"
    OTHER = "other"


class EventStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_name: str = Field(min_length=2, max_length=160)
    event_type: EventType
    event_date: datetime
    description: str = Field(default="", max_length=2_000)
    venue: str = Field(default="", max_length=300)
    start_time: str = Field(default="", max_length=20)
    end_time: str = Field(default="", max_length=20)
    status: EventStatus = EventStatus.DRAFT


class EventUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_name: str | None = Field(default=None, min_length=2, max_length=160)
    event_type: EventType | None = None
    event_date: datetime | None = None
    description: str | None = Field(default=None, max_length=2_000)
    venue: str | None = Field(default=None, max_length=300)
    start_time: str | None = Field(default=None, max_length=20)
    end_time: str | None = Field(default=None, max_length=20)
    status: EventStatus | None = None


class EventResponse(BaseModel):
    event_id: str
    event_name: str
    event_type: EventType
    description: str
    venue: str
    event_date: datetime
    start_time: str
    end_time: str
    status: EventStatus
    created_at: datetime
    updated_at: datetime
