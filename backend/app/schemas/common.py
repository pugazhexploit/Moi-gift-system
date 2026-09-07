"""Shared response schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: T
    message: str = "Operation successful"


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    request_id: str | None = Field(default=None)


class HealthData(BaseModel):
    status: str
    mongodb: str
    redis: str

