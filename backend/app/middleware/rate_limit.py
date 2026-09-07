"""Small in-memory safety limit; production can replace it with Redis storage."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, requests: int, window_seconds: int, login_requests: int, login_window_seconds: int) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.requests = requests
        self.window_seconds = window_seconds
        self.login_requests = login_requests
        self.login_window_seconds = login_window_seconds
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if request.url.path.endswith("/health"):
            return await call_next(request)  # type: ignore[operator]
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        is_login = request.url.path.endswith("/auth/login")
        key = f"{client}:login" if is_login else client
        limit = self.login_requests if is_login else self.requests
        window = self.login_window_seconds if is_login else self.window_seconds
        attempts = self._attempts[key]
        threshold = now - window
        while attempts and attempts[0] <= threshold:
            attempts.popleft()
        if len(attempts) >= limit:
            return JSONResponse(status_code=429, content={"success": False, "error": {"code": "RATE_LIMITED", "message": "Too many requests"}})
        attempts.append(now)
        return await call_next(request)  # type: ignore[operator]
