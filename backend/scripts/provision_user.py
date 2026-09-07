"""Provision a non-admin development or deployment user from environment variables.

Set USER_USERNAME, USER_EMAIL, USER_PASSWORD, and USER_ROLE (collector or viewer),
then run from backend: python -m scripts.provision_user
"""

from __future__ import annotations

import asyncio
import os

from app.core.config import get_settings
from app.core.database import database_manager
from app.models.user import UserRole
from app.schemas.auth import UserProvisionRequest
from app.services.auth_service import AuthenticationService


async def main() -> None:
    username = os.environ.get("USER_USERNAME")
    email = os.environ.get("USER_EMAIL")
    password = os.environ.get("USER_PASSWORD")
    role = os.environ.get("USER_ROLE")
    if not username or not email or not password or not role:
        raise RuntimeError("USER_USERNAME, USER_EMAIL, USER_PASSWORD, and USER_ROLE are required")
    payload = UserProvisionRequest(username=username, email=email, password=password, role=role)
    if payload.role is UserRole.ADMIN:
        raise RuntimeError("Use scripts.provision_admin for the initial administrator")
    settings = get_settings()
    settings.auth_secrets()
    await database_manager.connect(settings)
    try:
        if (await database_manager.health())["status"] != "available":
            raise RuntimeError("MongoDB is unavailable")
        service = AuthenticationService(database_manager.db, settings)
        user = await service.provision_user(payload.username, str(payload.email), payload.password, payload.role)
        print(f"Provisioned {payload.role.value} {user.username} ({user.user_id})")
    finally:
        await database_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
