"""Structured logging configuration with secret redaction."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.utils.redaction import redact


class JsonFormatter(logging.Formatter):
    """Format application log records as safe JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "user_id", "endpoint", "method", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(redact(payload), default=str, ensure_ascii=False)


def configure_logging(level: str) -> None:
    """Configure the GiftLedger logger once per process."""
    logger = logging.getLogger("giftledger")
    logger.setLevel(level.upper())
    logger.propagate = False

    if logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
