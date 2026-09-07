"""Audit log inspection endpoints for administrators."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.permissions import require_roles
from app.models.user import UserRole
from app.schemas.audit import AuditLogResponse
from app.schemas.common import SuccessResponse
from app.schemas.pagination import PaginatedData
from app.services.audit_service import AuditService


router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("", response_model=SuccessResponse[PaginatedData[AuditLogResponse]])
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    action: str | None = None,
    entity_type: str | None = None,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[PaginatedData[AuditLogResponse]]:
    items, total = await AuditService(request.app.state.database.db).list(
        page, limit, action, entity_type
    )
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))
