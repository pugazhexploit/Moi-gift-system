"""Admin endpoints for collector profiles and event assignment."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.permissions import request_context, require_roles
from app.models.user import UserRole
from app.schemas.collector import CollectorCreate, CollectorResponse, CollectorUpdate
from app.schemas.common import SuccessResponse
from app.schemas.pagination import PaginatedData
from app.services.collector_service import CollectorService


router = APIRouter(prefix="/collectors", tags=["Collectors"])


@router.get("", response_model=SuccessResponse[PaginatedData[CollectorResponse]])
async def list_collectors(request: Request, page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=100), user: dict = Depends(require_roles(UserRole.ADMIN))) -> SuccessResponse[PaginatedData[CollectorResponse]]:
    items, total = await CollectorService(request.app.state.database).list(page, limit)
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))


@router.post("", response_model=SuccessResponse[CollectorResponse])
async def create_collector(payload: CollectorCreate, request: Request, user: dict = Depends(require_roles(UserRole.ADMIN))) -> SuccessResponse[CollectorResponse]:
    collector = await CollectorService(request.app.state.database).create(payload, user, request_context(request))
    return SuccessResponse(data=collector, message="Collector created")


@router.patch("/{collector_id}", response_model=SuccessResponse[CollectorResponse])
async def update_collector(collector_id: str, payload: CollectorUpdate, request: Request, user: dict = Depends(require_roles(UserRole.ADMIN))) -> SuccessResponse[CollectorResponse]:
    collector = await CollectorService(request.app.state.database).update(collector_id, payload, user, request_context(request))
    return SuccessResponse(data=collector, message="Collector updated")
