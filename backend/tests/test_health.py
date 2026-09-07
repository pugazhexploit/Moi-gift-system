"""Foundation endpoint tests without requiring a live MongoDB server."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.main import create_app


def test_health_reports_degraded_when_mongodb_is_unavailable(monkeypatch: MonkeyPatch) -> None:
    app = create_app()

    async def unavailable() -> dict[str, str]:
        return {"status": "unavailable"}

    async def no_connect(_: object) -> None:
        return None

    async def no_close() -> None:
        return None

    monkeypatch.setattr("app.main.database_manager.health", unavailable)
    monkeypatch.setattr("app.main.database_manager.connect", no_connect)
    monkeypatch.setattr("app.main.database_manager.close", no_close)
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json()["data"]["mongodb"] == "unavailable"
    assert response.headers["x-request-id"]


def test_unknown_route_uses_safe_error_contract(monkeypatch: MonkeyPatch) -> None:
    app = create_app()

    async def no_connect(_: object) -> None:
        return None

    async def no_close() -> None:
        return None

    monkeypatch.setattr("app.main.database_manager.connect", no_connect)
    monkeypatch.setattr("app.main.database_manager.close", no_close)
    with TestClient(app) as client:
        response = client.get("/not-found")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Resource not found"
