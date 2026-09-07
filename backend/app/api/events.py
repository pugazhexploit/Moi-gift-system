"""Event endpoints with scoped read access and admin-only mutation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.permissions import get_current_user, request_context, require_roles
from app.models.user import UserRole
from app.schemas.common import SuccessResponse
from app.schemas.event import EventCreate, EventResponse, EventStatus, EventUpdate
from app.schemas.pagination import PaginatedData
from app.schemas.collector import AssignmentResponse
from app.services.collector_service import CollectorService
from app.services.event_service import EventService


router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=SuccessResponse[PaginatedData[EventResponse]])
async def list_events(request: Request, page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=100), search: str | None = Query(None, max_length=100), status: EventStatus | None = None, user: dict = Depends(get_current_user)) -> SuccessResponse[PaginatedData[EventResponse]]:
    items, total = await EventService(request.app.state.database).list(user, page, limit, search, status.value if status else None)
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))


@router.post("", response_model=SuccessResponse[EventResponse])
async def create_event(payload: EventCreate, request: Request, user: dict = Depends(require_roles(UserRole.ADMIN))) -> SuccessResponse[EventResponse]:
    event = await EventService(request.app.state.database).create(payload, user, request_context(request))
    return SuccessResponse(data=event, message="Event created")


@router.get("/{event_id}", response_model=SuccessResponse[EventResponse])
async def get_event(event_id: str, request: Request, user: dict = Depends(get_current_user)) -> SuccessResponse[EventResponse]:
    return SuccessResponse(data=await EventService(request.app.state.database).get(event_id, user))


@router.patch("/{event_id}", response_model=SuccessResponse[EventResponse])
async def update_event(event_id: str, payload: EventUpdate, request: Request, user: dict = Depends(require_roles(UserRole.ADMIN))) -> SuccessResponse[EventResponse]:
    event = await EventService(request.app.state.database).update(event_id, payload, user, request_context(request))
    return SuccessResponse(data=event, message="Event updated")


@router.post("/{event_id}/collectors/{collector_id}", response_model=SuccessResponse[AssignmentResponse])
async def assign_collector(event_id: str, collector_id: str, request: Request, user: dict = Depends(require_roles(UserRole.ADMIN))) -> SuccessResponse[AssignmentResponse]:
    assignment = await CollectorService(request.app.state.database).assign(event_id, collector_id, user, request_context(request))
    return SuccessResponse(data=assignment, message="Collector assigned")


@router.post("/{event_id}/viewers/{viewer_user_id}", response_model=SuccessResponse[EventResponse])
async def assign_viewer(event_id: str, viewer_user_id: str, request: Request, user: dict = Depends(require_roles(UserRole.ADMIN))) -> SuccessResponse[EventResponse]:
    event = await EventService(request.app.state.database).assign_viewer(event_id, viewer_user_id, user, request_context(request))
    return SuccessResponse(data=event, message="Viewer access granted")
