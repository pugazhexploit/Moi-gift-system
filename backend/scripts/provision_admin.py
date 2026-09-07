"""Create the initial administrator from environment variables.

Run from backend after setting ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD:
python -m scripts.provision_admin
Never use this command with a password recorded in shell history in production.
"""

from __future__ import annotations

import asyncio
import os

from app.core.config import get_settings
from app.core.database import database_manager
from app.schemas.auth import AdminProvisionRequest
from app.services.auth_service import AuthenticationService


async def main() -> None:
    username = os.environ.get("ADMIN_USERNAME")
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not username or not email or not password:
        raise RuntimeError("ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD are required")
    payload = AdminProvisionRequest(username=username, email=email, password=password)
    settings = get_settings()
    settings.auth_secrets()
    await database_manager.connect(settings)
    try:
        if (await database_manager.health())["status"] != "available":
            raise RuntimeError("MongoDB is unavailable")
        service = AuthenticationService(database_manager.db, settings)
        user = await service.provision_admin(payload.username, str(payload.email), payload.password)
        print(f"Provisioned administrator {user.username} ({user.user_id})")
    finally:
        await database_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
