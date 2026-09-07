"""Cookie-based authentication endpoints."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response

from app.core.exceptions import AppError
from app.core.permissions import get_current_user, request_context, require_csrf
from app.core.security import generate_csrf_token
from app.schemas.auth import LoginData, LoginRequest, PasswordChangeRequest, SessionData
from app.schemas.common import SuccessResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_session_cookies(response: Response, request: Request, access_token: str, refresh_token: str) -> None:
    settings = request.app.state.settings
    secure = settings.cookie_secure
    response.set_cookie(settings.access_cookie_name, access_token, max_age=settings.access_token_expire_minutes * 60, httponly=True, secure=secure, samesite=settings.cookie_samesite, path="/api")
    response.set_cookie(settings.refresh_cookie_name, refresh_token, max_age=settings.refresh_token_expire_days * 86_400, httponly=True, secure=secure, samesite=settings.cookie_samesite, path="/api/auth")
    response.set_cookie(settings.csrf_cookie_name, generate_csrf_token(), max_age=settings.refresh_token_expire_days * 86_400, httponly=False, secure=secure, samesite=settings.cookie_samesite, path="/")


def clear_session_cookies(response: Response, request: Request) -> None:
    settings = request.app.state.settings
    response.delete_cookie(settings.access_cookie_name, path="/api")
    response.delete_cookie(settings.refresh_cookie_name, path="/api/auth")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


from pymongo.errors import PyMongoError


@router.post("/login", response_model=SuccessResponse[LoginData])
async def login(payload: LoginRequest, request: Request, response: Response) -> SuccessResponse[LoginData]:
    auth_service = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        raise AppError("DATABASE_UNAVAILABLE", "Database service is unavailable. Please check MongoDB connection.", 503)
    try:
        user, access_token, refresh_token = await auth_service.login(payload.identifier, payload.password, request_context(request))
    except (RuntimeError, PyMongoError) as exc:
        raise AppError("DATABASE_UNAVAILABLE", "Database connection is unavailable. Please check MongoDB connection.", 503) from exc
    set_session_cookies(response, request, access_token, refresh_token)
    return SuccessResponse(data=LoginData(user=user), message="Login successful")


@router.post("/refresh", response_model=SuccessResponse[SessionData])
async def refresh(request: Request, response: Response) -> SuccessResponse[SessionData]:
    raw_token = request.cookies.get(request.app.state.settings.refresh_cookie_name)
    if not raw_token:
        raise AppError("AUTHENTICATION_REQUIRED", "Authentication is required", 401)
    user, access_token, refresh_token = await request.app.state.auth_service.refresh(raw_token, request_context(request))
    set_session_cookies(response, request, access_token, refresh_token)
    return SuccessResponse(data=SessionData(user=user), message="Session refreshed")


@router.post("/logout", response_model=SuccessResponse[dict[str, str]], dependencies=[Depends(require_csrf)])
async def logout(request: Request, response: Response) -> SuccessResponse[dict[str, str]]:
    raw_token = request.cookies.get(request.app.state.settings.refresh_cookie_name)
    await request.app.state.auth_service.logout(raw_token, request_context(request))
    clear_session_cookies(response, request)
    return SuccessResponse(data={"status": "logged_out"}, message="Logout successful")


@router.post("/password/change", response_model=SuccessResponse[dict[str, str]], dependencies=[Depends(require_csrf)])
async def change_password(payload: PasswordChangeRequest, request: Request, response: Response, user: dict = Depends(get_current_user)) -> SuccessResponse[dict[str, str]]:
    await request.app.state.auth_service.change_password(user, payload.current_password, payload.new_password, request_context(request))
    clear_session_cookies(response, request)
    return SuccessResponse(data={"status": "password_changed"}, message="Password changed; please sign in again")
