"""Request correlation middleware."""

from __future__ import annotations

import time
from uuid import uuid4

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger("giftledger")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)  # type: ignore[operator]
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info("request completed", extra={"request_id": request_id, "endpoint": request.url.path, "method": request.method, "status_code": response.status_code, "duration_ms": duration_ms})
        return response
