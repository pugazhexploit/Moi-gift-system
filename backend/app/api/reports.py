"""Dashboard, report, and audited export endpoints."""

from __future__ import annotations

import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.core.permissions import get_current_user, request_context, require_csrf, require_roles
from app.models.user import UserRole
from app.schemas.common import SuccessResponse
from app.schemas.pagination import PaginatedData
from app.schemas.report import (
    CollectorReport,
    DashboardData,
    EventReport,
    ExportFormat,
    GuestReportItem,
    ReconciliationReportItem,
)
from app.services.export_service import ExportFile
from app.services.report_service import ReportService


dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
router = APIRouter(prefix="/reports", tags=["Reports"])


@dashboard_router.get("", response_model=SuccessResponse[DashboardData])
async def dashboard(
    request: Request,
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[DashboardData]:
    data = await ReportService(request.app.state.database).dashboard(
        user, event_id, start_at, end_at
    )
    return SuccessResponse(data=data)


@router.get("/event/{event_id}", response_model=SuccessResponse[EventReport])
async def event_report(
    event_id: str, request: Request, user: dict = Depends(get_current_user)
) -> SuccessResponse[EventReport]:
    return SuccessResponse(
        data=await ReportService(request.app.state.database).event_report(event_id, user)
    )


@router.get("/collector/{collector_id}", response_model=SuccessResponse[CollectorReport])
async def collector_report(
    collector_id: str,
    request: Request,
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    user: dict = Depends(get_current_user),
) -> SuccessResponse[CollectorReport]:
    return SuccessResponse(
        data=await ReportService(request.app.state.database).collector_report(
            collector_id, user, event_id
        )
    )


@router.get("/guests", response_model=SuccessResponse[PaginatedData[GuestReportItem]])
async def guest_report(
    request: Request,
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    user: dict = Depends(get_current_user),
) -> SuccessResponse[PaginatedData[GuestReportItem]]:
    items, total = await ReportService(request.app.state.database).guest_report(
        user, event_id, page, limit
    )
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))


@router.get("/reconciliation", response_model=SuccessResponse[PaginatedData[ReconciliationReportItem]])
async def reconciliation_report(
    request: Request,
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    user: dict = Depends(get_current_user),
) -> SuccessResponse[PaginatedData[ReconciliationReportItem]]:
    items, total = await ReportService(request.app.state.database).reconciliation_report(
        user, event_id, page, limit
    )
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))


@router.post(
    "/event/{event_id}/export",
    dependencies=[Depends(require_csrf)],
    response_class=StreamingResponse,
)
async def export_event_report(
    event_id: str,
    request: Request,
    export_format: ExportFormat = Query(alias="format"),
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> StreamingResponse:
    export = await ReportService(request.app.state.database).export_event(
        event_id, export_format, user, request_context(request)
    )
    return _export_response(export)


@router.post(
    "/collector/{collector_id}/export",
    dependencies=[Depends(require_csrf)],
    response_class=StreamingResponse,
)
async def export_collector_report(
    collector_id: str,
    request: Request,
    export_format: ExportFormat = Query(alias="format"),
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> StreamingResponse:
    export = await ReportService(request.app.state.database).export_collector(
        collector_id, event_id, export_format, user, request_context(request)
    )
    return _export_response(export)


@router.post(
    "/guests/export",
    dependencies=[Depends(require_csrf)],
    response_class=StreamingResponse,
)
async def export_guest_report(
    request: Request,
    export_format: ExportFormat = Query(alias="format"),
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> StreamingResponse:
    export = await ReportService(request.app.state.database).export_guests(
        event_id, export_format, user, request_context(request)
    )
    return _export_response(export)


@router.post(
    "/reconciliation/export",
    dependencies=[Depends(require_csrf)],
    response_class=StreamingResponse,
)
async def export_reconciliation_report(
    request: Request,
    export_format: ExportFormat = Query(alias="format"),
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> StreamingResponse:
    export = await ReportService(request.app.state.database).export_reconciliations(
        event_id, export_format, user, request_context(request)
    )
    return _export_response(export)


def _export_response(export: ExportFile) -> StreamingResponse:
    return StreamingResponse(
        io.BytesIO(export.content),
        media_type=export.media_type,
        headers={"Content-Disposition": f'attachment; filename="{export.filename}"'},
    )
