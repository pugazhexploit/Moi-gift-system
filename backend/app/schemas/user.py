"""User management schemas for admin operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailStr
    role: UserRole = UserRole.COLLECTOR


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    username: str
    email: str
    role: UserRole
    status: UserStatus
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: UserRole


class UserStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: UserStatus
