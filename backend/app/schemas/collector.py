"""Collector and assignment schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CollectorStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class CollectorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: str = Field(min_length=24, max_length=24)
    name: str = Field(min_length=2, max_length=160)
    phone: str = Field(default="", max_length=32)
    employee_code: str = Field(default="", max_length=64)
    status: CollectorStatus = CollectorStatus.ACTIVE


class CollectorUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    employee_code: str | None = Field(default=None, max_length=64)
    status: CollectorStatus | None = None


class CollectorResponse(BaseModel):
    collector_id: str
    name: str
    phone: str
    employee_code: str
    status: CollectorStatus
    created_at: datetime
    updated_at: datetime


class AssignmentResponse(BaseModel):
    event_id: str
    collector_id: str
    assigned_at: datetime
    status: str
