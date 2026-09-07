"""Authentication orchestration with password, session, and audit controls."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4

from bson import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure, PyMongoError

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.security import (create_access_token, generate_refresh_token, hash_password, hash_refresh_token, password_needs_rehash, utc_now, verify_password)
from app.models.user import UserRole, UserStatus
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.schemas.auth import AuthenticatedUser
from app.services.audit_service import AuditService


class AuthenticationService:
    def __init__(self, database: Any, settings: Settings) -> None:
        self.database = database
        self.settings = settings
        self.users = UserRepository(database)
        self.refresh_tokens = RefreshTokenRepository(database)
        self.audit = AuditService(database)

    @staticmethod
    def safe_user(user: dict[str, Any]) -> AuthenticatedUser:
        return AuthenticatedUser(user_id=str(user["_id"]), username=user["username"], email=user["email"], role=UserRole(user["role"]), last_login_at=user.get("last_login_at"))

    async def provision_admin(self, username: str, email: str, password: str) -> AuthenticatedUser:
        return await self.provision_user(username, email, password, UserRole.ADMIN)

    async def provision_user(self, username: str, email: str, password: str, role: UserRole) -> AuthenticatedUser:
        now = utc_now()
        async def create(session: Any) -> dict[str, Any]:
            user = await self.users.create_user(username.strip(), email.strip().casefold(), hash_password(password), role, now, session=session)
            await self.audit.record(user_id=user["_id"], action="CREATE", request_id=None, ip_address=None, user_agent=None, new_value={"role": role.value}, session=session)
            return user
        try:
            user = await self._with_transaction(create)
        except DuplicateKeyError as exc:
            raise AppError("USER_EXISTS", "Username or email is already registered", 409) from exc
        return self.safe_user(user)

    async def login(self, identifier: str, password: str, request_context: dict[str, str | None]) -> tuple[AuthenticatedUser, str, str]:
        now = utc_now()
        user = await self.users.get_by_identifier(identifier)
        if user is None or user.get("status") != UserStatus.ACTIVE.value:
            # Argon2 work is performed to make unknown-user attempts less distinguishable.
            verify_password(password, hash_password("not-the-request-password"))
            raise AppError("INVALID_CREDENTIALS", "Invalid username/email or password", 401)

        locked_until = user.get("locked_until")
        if locked_until is not None and locked_until > now:
            raise AppError("ACCOUNT_LOCKED", "Account is temporarily locked", 423)

        if not verify_password(password, user["password_hash"]):
            attempts = await self.users.increment_failed_login(user["_id"], now)
            if attempts >= self.settings.login_max_attempts:
                await self.users.lock_account(user["_id"], now + timedelta(minutes=self.settings.login_lockout_minutes), now)
            raise AppError("INVALID_CREDENTIALS", "Invalid username/email or password", 401)

        upgraded_hash = hash_password(password) if password_needs_rehash(user["password_hash"]) else None
        async def establish_session(session: Any) -> tuple[str, str]:
            await self.users.record_successful_login(user["_id"], now, upgraded_hash, session=session)
            refresh_token, _ = await self._create_session(user["_id"], session=session)
            await self.audit.record(user_id=user["_id"], action="LOGIN", request_id=request_context.get("request_id"), ip_address=request_context.get("ip_address"), user_agent=request_context.get("user_agent"), session=session)
            return refresh_token, ""
        refresh_token, _ = await self._with_transaction(establish_session)
        user["last_login_at"] = now
        if upgraded_hash:
            user["password_hash"] = upgraded_hash
        access_token = create_access_token(self.settings, str(user["_id"]), UserRole(user["role"]))
        return self.safe_user(user), access_token, refresh_token

    async def refresh(self, raw_token: str, request_context: dict[str, str | None]) -> tuple[AuthenticatedUser, str, str]:
        token_hash = hash_refresh_token(self.settings, raw_token)
        existing = await self.refresh_tokens.get(token_hash)
        now = utc_now()
        if existing is None:
            raise AppError("INVALID_SESSION", "Session is invalid or expired", 401)
        if existing.get("revoked_at") is not None or existing.get("expires_at") <= now:
            await self.refresh_tokens.revoke_family(existing["family_id"], now)
            raise AppError("INVALID_SESSION", "Session is invalid or expired", 401)

        replacement = generate_refresh_token()
        replacement_hash = hash_refresh_token(self.settings, replacement)
        async def rotate(session: Any) -> dict[str, Any] | None:
            consumed = await self.refresh_tokens.consume(token_hash, now, replacement_hash, session=session)
            if consumed is None:
                return None
            await self.refresh_tokens.create(replacement_hash, consumed["user_id"], consumed["family_id"], now, now + timedelta(days=self.settings.refresh_token_expire_days), session=session)
            await self.audit.record(user_id=consumed["user_id"], action="REFRESH", request_id=request_context.get("request_id"), ip_address=request_context.get("ip_address"), user_agent=request_context.get("user_agent"), session=session)
            return consumed
        consumed = await self._with_transaction(rotate)
        if consumed is None:
            await self.refresh_tokens.revoke_family(existing["family_id"], now)
            raise AppError("INVALID_SESSION", "Session is invalid or expired", 401)
        user = await self.users.get_by_id(str(consumed["user_id"]))
        if user is None or user.get("status") != UserStatus.ACTIVE.value:
            await self.refresh_tokens.revoke_family(consumed["family_id"], now)
            raise AppError("INVALID_SESSION", "Session is invalid or expired", 401)
        access_token = create_access_token(self.settings, str(user["_id"]), UserRole(user["role"]))
        return self.safe_user(user), access_token, replacement

    async def logout(self, raw_token: str | None, request_context: dict[str, str | None], user_id: ObjectId | None = None) -> None:
        if raw_token:
            token = await self.refresh_tokens.get(hash_refresh_token(self.settings, raw_token))
            if token is not None:
                now = utc_now()
                async def revoke(session: Any) -> None:
                    await self.refresh_tokens.revoke_family(token["family_id"], now, session=session)
                    await self.audit.record(user_id=token["user_id"], action="LOGOUT", request_id=request_context.get("request_id"), ip_address=request_context.get("ip_address"), user_agent=request_context.get("user_agent"), session=session)
                await self._with_transaction(revoke)
                user_id = token["user_id"]
        if user_id is not None and not raw_token:
            await self.audit.record(user_id=user_id, action="LOGOUT", request_id=request_context.get("request_id"), ip_address=request_context.get("ip_address"), user_agent=request_context.get("user_agent"))

    async def change_password(self, user: dict[str, Any], current_password: str, new_password: str, request_context: dict[str, str | None]) -> None:
        if not verify_password(current_password, user["password_hash"]):
            raise AppError("INVALID_CREDENTIALS", "Current password is incorrect", 401)
        if verify_password(new_password, user["password_hash"]):
            raise AppError("VALIDATION_ERROR", "New password must be different", 422)
        now = utc_now()
        new_hash = hash_password(new_password)
        async def change(session: Any) -> None:
            await self.users.change_password(user["_id"], new_hash, now, session=session)
            await self.refresh_tokens.revoke_user_tokens(user["_id"], now, session=session)
            await self.audit.record(user_id=user["_id"], action="PASSWORD_CHANGE", request_id=request_context.get("request_id"), ip_address=request_context.get("ip_address"), user_agent=request_context.get("user_agent"), session=session)
        await self._with_transaction(change)

    async def _create_session(self, user_id: ObjectId, session: Any = None) -> tuple[str, str]:
        now = utc_now()
        raw_token = generate_refresh_token()
        token_hash = hash_refresh_token(self.settings, raw_token)
        family_id = str(uuid4())
        await self.refresh_tokens.create(token_hash, user_id, family_id, now, now + timedelta(days=self.settings.refresh_token_expire_days), session=session)
        return raw_token, family_id

    async def _with_transaction(self, callback: Any) -> Any:
        """Run auth state and its audit event atomically on MongoDB replica set, or directly on standalone."""
        try:
            session = self.database.client.start_session()
            if hasattr(session, "__await__") and not hasattr(session, "__aenter__"):
                session = await session
            async with session as s:
                return await s.with_transaction(callback)
        except (OperationFailure, PyMongoError) as exc:
            if getattr(exc, "code", None) == 20 or "replica set" in str(exc).lower() or "transaction" in str(exc).lower():
                return await callback(None)
            raise
