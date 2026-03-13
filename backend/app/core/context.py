"""Request-scoped context variables."""

from __future__ import annotations

from contextvars import ContextVar

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
model_profile_context: ContextVar[str] = ContextVar("model_profile", default="-")

