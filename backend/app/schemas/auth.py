"""Strict request and safe response schemas for authentication."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    identifier: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class AdminProvisionRequest(BaseModel):
    """CLI-only initial administrator input validation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: str = Field(pattern=r"^[A-Za-z0-9_.-]{3,64}$")
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserProvisionRequest(AdminProvisionRequest):
    role: UserRole


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if any(character.isspace() and character not in {" "} for character in value):
            raise ValueError("Password contains unsupported whitespace")
        if any(ord(character) < 32 for character in value):
            raise ValueError("Password contains control characters")
        return value


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    username: str
    email: EmailStr
    role: UserRole
    last_login_at: datetime | None = None


class LoginData(BaseModel):
    user: AuthenticatedUser


class SessionData(BaseModel):
    user: AuthenticatedUser
