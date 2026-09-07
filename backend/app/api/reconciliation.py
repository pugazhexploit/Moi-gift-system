"""Cash reconciliation endpoints with collector ownership and admin controls."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.permissions import get_current_user, request_context, require_csrf, require_roles
from app.models.user import UserRole
from app.schemas.common import SuccessResponse
from app.schemas.pagination import PaginatedData
from app.schemas.reconciliation import (
    ReconciliationAction,
    ReconciliationCreate,
    ReconciliationResponse,
    ReconciliationStatus,
)
from app.services.reconciliation_service import ReconciliationService


router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.get("", response_model=SuccessResponse[PaginatedData[ReconciliationResponse]])
async def list_reconciliations(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    status: ReconciliationStatus | None = None,
    user: dict = Depends(get_current_user),
) -> SuccessResponse[PaginatedData[ReconciliationResponse]]:
    items, total = await ReconciliationService(request.app.state.database).list(
        user, page, limit, event_id, status
    )
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))


@router.post("", response_model=SuccessResponse[ReconciliationResponse], dependencies=[Depends(require_csrf)])
async def create_reconciliation(
    payload: ReconciliationCreate,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.COLLECTOR)),
) -> SuccessResponse[ReconciliationResponse]:
    reconciliation = await ReconciliationService(request.app.state.database).create(
        payload, user, request_context(request)
    )
    return SuccessResponse(data=reconciliation, message="Reconciliation submitted")


@router.get("/{reconciliation_id}", response_model=SuccessResponse[ReconciliationResponse])
async def get_reconciliation(
    reconciliation_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
) -> SuccessResponse[ReconciliationResponse]:
    return SuccessResponse(
        data=await ReconciliationService(request.app.state.database).get(reconciliation_id, user)
    )


@router.post(
    "/{reconciliation_id}/verify",
    response_model=SuccessResponse[ReconciliationResponse],
    dependencies=[Depends(require_csrf)],
)
async def verify_reconciliation(
    reconciliation_id: str,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[ReconciliationResponse]:
    reconciliation = await ReconciliationService(request.app.state.database).verify(
        reconciliation_id, user, request_context(request)
    )
    return SuccessResponse(data=reconciliation, message="Reconciliation verified")


@router.post(
    "/{reconciliation_id}/resolve",
    response_model=SuccessResponse[ReconciliationResponse],
    dependencies=[Depends(require_csrf)],
)
async def resolve_reconciliation(
    reconciliation_id: str,
    action: ReconciliationAction,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[ReconciliationResponse]:
    reconciliation = await ReconciliationService(request.app.state.database).resolve(
        reconciliation_id, action, user, request_context(request)
    )
    return SuccessResponse(data=reconciliation, message="Reconciliation resolved")
