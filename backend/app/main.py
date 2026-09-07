"""GiftLedger FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.collectors import router as collectors_router
from app.api.events import router as events_router
from app.api.gifts import router as gifts_router
from app.api.guests import router as guests_router
from app.api.reconciliation import router as reconciliation_router
from app.api.reports import dashboard_router, router as reports_router
from app.api.transactions import receipts_router, router as transactions_router
from app.api.users import router as users_router
from app.api.audit import router as audit_router
from app.core.config import get_settings
from app.core.database import database_manager
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.rate_limit import InMemoryRateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.auth_service import AuthenticationService


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.database = database_manager
        await database_manager.connect(settings)
        app.state.auth_service = (
            AuthenticationService(database_manager.db, settings)
            if database_manager.client is not None
            else None
        )
        yield
        await database_manager.close()

    app = FastAPI(title="GiftLedger API", version="0.1.0", lifespan=lifespan, docs_url="/docs" if settings.environment != "production" else None, redoc_url=None)
    app.state.settings = settings
    app.state.database = database_manager
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID", "Idempotency-Key"])
    app.add_middleware(InMemoryRateLimitMiddleware, requests=settings.general_rate_limit_requests, window_seconds=settings.general_rate_limit_window_seconds, login_requests=settings.login_rate_limit_requests, login_window_seconds=settings.login_rate_limit_window_seconds)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(events_router, prefix=settings.api_prefix)
    app.include_router(guests_router, prefix=settings.api_prefix)
    app.include_router(collectors_router, prefix=settings.api_prefix)
    app.include_router(transactions_router, prefix=settings.api_prefix)
    app.include_router(receipts_router, prefix=settings.api_prefix)
    app.include_router(gifts_router, prefix=settings.api_prefix)
    app.include_router(reconciliation_router, prefix=settings.api_prefix)
    app.include_router(dashboard_router, prefix=settings.api_prefix)
    app.include_router(reports_router, prefix=settings.api_prefix)
    app.include_router(users_router, prefix=settings.api_prefix)
    app.include_router(audit_router, prefix=settings.api_prefix)
    return app


app = create_app()
