"""Admin user management service."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import AppError
from app.core.security import hash_password, utc_now
from app.models.user import UserRole, UserStatus
from app.repositories.users import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserRoleUpdate, UserStatusUpdate
from app.services.audit_service import AuditService


class UserService:
    def __init__(self, database: Any) -> None:
        self.users = UserRepository(database)
        self.audit = AuditService(database)

    async def list(self, page: int, limit: int, role: str | None = None) -> tuple[list[UserResponse], int]:
        items, total = await self.users.list_users(page, limit, role)
        return [self.to_response(u) for u in items], total

    async def create(self, payload: UserCreate, admin_user: dict[str, Any], context: dict[str, str | None]) -> UserResponse:
        existing = await self.users.get_by_identifier(payload.username) or await self.users.get_by_identifier(payload.email)
        if existing is not None:
            raise AppError("CONFLICT", "Username or email already exists", 409)

        hashed = hash_password(payload.password)
        now = utc_now()
        try:
            user = await self.users.create_user(
                username=payload.username,
                email=payload.email,
                password_hash=hashed,
                role=payload.role,
                now=now,
            )
        except DuplicateKeyError as exc:
            raise AppError("CONFLICT", "Username or email already registered", 409) from exc

        await self.audit.record(
            user_id=admin_user["_id"],
            action="CREATE",
            request_id=context.get("request_id"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            entity_type="user",
            entity_id=user["_id"],
            new_value={"username": user["username"], "role": user["role"]},
        )
        return self.to_response(user)

    async def update_role(self, user_id: str, payload: UserRoleUpdate, admin_user: dict[str, Any], context: dict[str, str | None]) -> UserResponse:
        if not ObjectId.is_valid(user_id):
            raise AppError("RESOURCE_NOT_FOUND", "User not found", 404)
        target_oid = ObjectId(user_id)
        if target_oid == admin_user["_id"] and payload.role != UserRole.ADMIN:
            raise AppError("FORBIDDEN", "Admins cannot remove their own admin role", 403)

        updated = await self.users.update_role(target_oid, payload.role, utc_now())
        if updated is None:
            raise AppError("RESOURCE_NOT_FOUND", "User not found", 404)

        await self.audit.record(
            user_id=admin_user["_id"],
            action="ROLE_CHANGE",
            request_id=context.get("request_id"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            entity_type="user",
            entity_id=updated["_id"],
            new_value={"new_role": payload.role.value},
        )
        return self.to_response(updated)

    async def update_status(self, user_id: str, payload: UserStatusUpdate, admin_user: dict[str, Any], context: dict[str, str | None]) -> UserResponse:
        if not ObjectId.is_valid(user_id):
            raise AppError("RESOURCE_NOT_FOUND", "User not found", 404)
        target_oid = ObjectId(user_id)
        if target_oid == admin_user["_id"] and payload.status != UserStatus.ACTIVE:
            raise AppError("FORBIDDEN", "Admins cannot deactivate their own account", 403)

        updated = await self.users.update_status(target_oid, payload.status, utc_now())
        if updated is None:
            raise AppError("RESOURCE_NOT_FOUND", "User not found", 404)

        await self.audit.record(
            user_id=admin_user["_id"],
            action="UPDATE",
            request_id=context.get("request_id"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            entity_type="user",
            entity_id=updated["_id"],
            new_value={"new_status": payload.status.value},
        )
        return self.to_response(updated)

    @staticmethod
    def to_response(user: dict[str, Any]) -> UserResponse:
        return UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            role=UserRole(user["role"]),
            status=UserStatus(user["status"]),
            last_login_at=user.get("last_login_at"),
            created_at=user["created_at"],
            updated_at=user["updated_at"],
        )
