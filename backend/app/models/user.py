"""User role constants shared by authentication and authorization."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    COLLECTOR = "collector"
    VIEWER = "viewer"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
