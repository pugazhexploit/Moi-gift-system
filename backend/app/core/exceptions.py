"""Safe API exceptions and centralized exception handlers."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger("giftledger")


class AppError(Exception):
    """An expected, safe-to-return API error."""

    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def error_response(code: str, message: str, status_code: int, request: Request) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    body: dict[str, Any] = {"success": False, "error": {"code": code, "message": message}}
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers that never disclose implementation details."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.code, exc.message, exc.status_code, request)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.info(
            "request validation failed",
            extra={"request_id": getattr(request.state, "request_id", None), "endpoint": request.url.path},
        )
        return error_response("VALIDATION_ERROR", "Invalid request", status.HTTP_422_UNPROCESSABLE_ENTITY, request)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        messages = {404: "Resource not found", 405: "Method not allowed"}
        return error_response("HTTP_ERROR", messages.get(exc.status_code, "Request could not be completed"), exc.status_code, request)

    from pymongo.errors import PyMongoError

    @app.exception_handler(PyMongoError)
    async def handle_database_error(request: Request, exc: PyMongoError) -> JSONResponse:
        logger.error(
            "database error: %s", exc,
            extra={"request_id": getattr(request.state, "request_id", None), "endpoint": request.url.path},
        )
        return error_response(
            "DATABASE_UNAVAILABLE",
            "Database connection unavailable. Please check MongoDB connection and Atlas IP whitelist.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            request,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled application error",
            extra={"request_id": getattr(request.state, "request_id", None), "endpoint": request.url.path},
        )
        return error_response("INTERNAL_ERROR", "An unexpected error occurred", status.HTTP_500_INTERNAL_SERVER_ERROR, request)
