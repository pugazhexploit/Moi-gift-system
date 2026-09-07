"""Reusable server-side authentication, CSRF, and role dependencies."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, Request

from app.core.exceptions import AppError
from app.core.security import InvalidTokenError, csrf_tokens_match, decode_access_token
from app.models.user import UserRole, UserStatus


def request_context(request: Request) -> dict[str, str | None]:
    return {"request_id": getattr(request.state, "request_id", None), "ip_address": request.client.host if request.client else None, "user_agent": request.headers.get("user-agent")}


async def get_current_user(request: Request) -> dict[str, Any]:
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    else:
        token = request.cookies.get(request.app.state.settings.access_cookie_name)
    if not token:
        raise AppError("AUTHENTICATION_REQUIRED", "Authentication is required", 401)
    try:
        payload = decode_access_token(request.app.state.settings, token)
    except (InvalidTokenError, RuntimeError) as exc:
        raise AppError("INVALID_TOKEN", "Session is invalid or expired", 401) from exc
    user = await request.app.state.auth_service.users.get_by_id(payload["sub"])
    if user is None or user.get("status") != UserStatus.ACTIVE.value:
        raise AppError("AUTHENTICATION_REQUIRED", "Authentication is required", 401)
    return user


async def require_csrf(request: Request) -> None:
    if request.headers.get("authorization", "").startswith("Bearer "):
        return
    header = request.headers.get("X-CSRF-Token")
    cookie = request.cookies.get(request.app.state.settings.csrf_cookie_name)
    if not csrf_tokens_match(header, cookie):
        raise AppError("CSRF_FAILED", "CSRF validation failed", 403)


def require_roles(*roles: UserRole) -> Callable[..., Any]:
    async def dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if UserRole(user["role"]) not in roles:
            raise AppError("FORBIDDEN", "You are not allowed to perform this action", 403)
        return user
    return dependency
