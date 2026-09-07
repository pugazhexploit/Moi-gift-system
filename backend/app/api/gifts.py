"""Physical gift endpoints with collector ownership protections."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.permissions import get_current_user, request_context, require_csrf, require_roles
from app.models.user import UserRole
from app.schemas.common import SuccessResponse
from app.schemas.gift import GiftCreate, GiftResponse, GiftUpdate
from app.schemas.pagination import PaginatedData
from app.services.gift_service import GiftService


router = APIRouter(prefix="/gifts", tags=["Gifts"])


@router.get("", response_model=SuccessResponse[PaginatedData[GiftResponse]])
async def list_gifts(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    user: dict = Depends(get_current_user),
) -> SuccessResponse[PaginatedData[GiftResponse]]:
    items, total = await GiftService(request.app.state.database).list(user, page, limit, event_id)
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))


@router.post("", response_model=SuccessResponse[GiftResponse], dependencies=[Depends(require_csrf)])
async def create_gift(
    payload: GiftCreate,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.COLLECTOR)),
) -> SuccessResponse[GiftResponse]:
    gift = await GiftService(request.app.state.database).create(payload, user, request_context(request))
    return SuccessResponse(data=gift, message="Gift recorded")


@router.get("/{gift_id}", response_model=SuccessResponse[GiftResponse])
async def get_gift(
    gift_id: str, request: Request, user: dict = Depends(get_current_user)
) -> SuccessResponse[GiftResponse]:
    return SuccessResponse(data=await GiftService(request.app.state.database).get(gift_id, user))


@router.patch("/{gift_id}", response_model=SuccessResponse[GiftResponse], dependencies=[Depends(require_csrf)])
async def update_gift(
    gift_id: str,
    payload: GiftUpdate,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.COLLECTOR)),
) -> SuccessResponse[GiftResponse]:
    gift = await GiftService(request.app.state.database).update(
        gift_id, payload, user, request_context(request)
    )
    return SuccessResponse(data=gift, message="Gift updated")
