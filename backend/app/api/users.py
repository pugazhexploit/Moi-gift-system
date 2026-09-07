"""User management endpoints for administrator role."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.permissions import request_context, require_csrf, require_roles
from app.models.user import UserRole
from app.schemas.common import SuccessResponse
from app.schemas.pagination import PaginatedData
from app.schemas.user import UserCreate, UserResponse, UserRoleUpdate, UserStatusUpdate
from app.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=SuccessResponse[PaginatedData[UserResponse]])
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    role: UserRole | None = None,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[PaginatedData[UserResponse]]:
    items, total = await UserService(request.app.state.database.db).list(
        page, limit, role.value if role else None
    )
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))


@router.post("", response_model=SuccessResponse[UserResponse], dependencies=[Depends(require_csrf)])
async def create_user(
    payload: UserCreate,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[UserResponse]:
    created = await UserService(request.app.state.database.db).create(
        payload, user, request_context(request)
    )
    return SuccessResponse(data=created, message="User created successfully")


@router.patch("/{user_id}/role", response_model=SuccessResponse[UserResponse], dependencies=[Depends(require_csrf)])
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[UserResponse]:
    updated = await UserService(request.app.state.database.db).update_role(
        user_id, payload, user, request_context(request)
    )
    return SuccessResponse(data=updated, message="Role updated")


@router.patch("/{user_id}/status", response_model=SuccessResponse[UserResponse], dependencies=[Depends(require_csrf)])
async def update_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[UserResponse]:
    updated = await UserService(request.app.state.database.db).update_status(
        user_id, payload, user, request_context(request)
    )
    return SuccessResponse(data=updated, message="Status updated")
