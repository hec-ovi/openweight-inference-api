"""JSON structured logging setup."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from pythonjsonlogger.json import JsonFormatter

from app.core.context import model_profile_context, request_id_context


class GatewayJsonFormatter(JsonFormatter):
    """Attach request and model context to structured logs."""

    def add_fields(self, log_record: dict[str, object], record: logging.LogRecord, message_dict: dict[str, object]) -> None:
        """Inject standard JSON fields."""

        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(UTC).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["message"] = record.getMessage()
        log_record["request_id"] = request_id_context.get()
        log_record["model_profile"] = model_profile_context.get()


def configure_logging(level: str) -> None:
    """Configure root logging once per process."""

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(GatewayJsonFormatter())

    root_logger.setLevel(level.upper())
    root_logger.addHandler(handler)

