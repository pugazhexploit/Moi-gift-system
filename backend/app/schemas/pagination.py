"""Validated server-side pagination models."""

from __future__ import annotations

from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class PageParameters(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=25, ge=1, le=100)


class PageMeta(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    pagination: PageMeta

    @classmethod
    def build(cls, items: list[T], page: int, limit: int, total: int) -> "PaginatedData[T]":
        return cls(items=items, pagination=PageMeta(page=page, limit=limit, total=total, pages=ceil(total / limit) if total else 0))
