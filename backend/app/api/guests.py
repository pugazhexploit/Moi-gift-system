"""Guest APIs with event-level BOLA protections."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.permissions import get_current_user, request_context
from app.schemas.common import SuccessResponse
from app.schemas.guest import GuestCreate, GuestQrResponse, GuestResponse, GuestUpdate
from app.schemas.pagination import PaginatedData
from app.services.guest_service import GuestService


router = APIRouter(prefix="/guests", tags=["Guests"])


@router.get("", response_model=SuccessResponse[PaginatedData[GuestResponse]])
async def list_guests(request: Request, page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=100), search: str | None = Query(None, max_length=100), event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"), user: dict = Depends(get_current_user)) -> SuccessResponse[PaginatedData[GuestResponse]]:
    items, total = await GuestService(request.app.state.database).list(user, page, limit, search, event_id)
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))


@router.post("", response_model=SuccessResponse[GuestResponse])
async def create_guest(payload: GuestCreate, request: Request, user: dict = Depends(get_current_user)) -> SuccessResponse[GuestResponse]:
    guest = await GuestService(request.app.state.database).create(payload, user, request_context(request))
    return SuccessResponse(data=guest, message="Guest created")


@router.get("/scan/{qr_token}", response_model=SuccessResponse[GuestResponse])
async def scan_guest(qr_token: str, request: Request, user: dict = Depends(get_current_user)) -> SuccessResponse[GuestResponse]:
    return SuccessResponse(data=await GuestService(request.app.state.database).scan(qr_token, user))


@router.get("/{guest_id}", response_model=SuccessResponse[GuestResponse])
async def get_guest(guest_id: str, request: Request, user: dict = Depends(get_current_user)) -> SuccessResponse[GuestResponse]:
    return SuccessResponse(data=await GuestService(request.app.state.database).get(guest_id, user))


@router.patch("/{guest_id}", response_model=SuccessResponse[GuestResponse])
async def update_guest(guest_id: str, payload: GuestUpdate, request: Request, user: dict = Depends(get_current_user)) -> SuccessResponse[GuestResponse]:
    guest = await GuestService(request.app.state.database).update(guest_id, payload, user, request_context(request))
    return SuccessResponse(data=guest, message="Guest updated")


@router.get("/{guest_id}/qr", response_model=SuccessResponse[GuestQrResponse])
async def guest_qr(guest_id: str, request: Request, user: dict = Depends(get_current_user)) -> SuccessResponse[GuestQrResponse]:
    return SuccessResponse(data=await GuestService(request.app.state.database).qr_token(guest_id, user))
