"""Non-sensitive service health endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse


router = APIRouter(tags=["Health"])


@router.get("/health", summary="Check application dependencies")
async def health_check(request: Request) -> JSONResponse:
    database = await request.app.state.database.health()
    mongodb_status = database["status"]
    redis_status = "not_configured" if request.app.state.settings.redis_url is None else "not_checked"
    overall = "healthy" if mongodb_status == "available" else "degraded"
    data_payload: dict[str, str] = {"status": overall, "mongodb": mongodb_status, "redis": redis_status}
    if "detail" in database:
        data_payload["mongodb_detail"] = database["detail"]
    body = {"success": True, "data": data_payload, "message": "Health check complete"}
    return JSONResponse(status_code=status.HTTP_200_OK if overall == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE, content=body)
