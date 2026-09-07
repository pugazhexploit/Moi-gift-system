"""Initialize GiftLedger MongoDB validators and indexes.

Run with (from the backend directory): python -m scripts.create_indexes
MongoDB must be available and configured through backend/.env or environment variables.
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.database import database_manager


async def main() -> None:
    settings = get_settings()
    await database_manager.connect(settings)
    try:
        status = await database_manager.health()
        if status["status"] != "available":
            raise RuntimeError("MongoDB is unavailable; schema initialization was not attempted")
        await database_manager.initialize_database()
    finally:
        await database_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
