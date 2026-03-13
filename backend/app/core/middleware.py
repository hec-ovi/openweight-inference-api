"""ASGI middleware for request IDs, logging, and request limits."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import get_settings
from app.core.context import model_profile_context, request_id_context
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.models.errors import ErrorDetails, ErrorEnvelope

logger = logging.getLogger("openweight.access")


class RequestContextMiddleware:
    """Attach request IDs and active model profile context."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Set request-scoped context and inject `X-Request-ID` headers."""

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.decode("latin-1"): value.decode("latin-1") for key, value in scope["headers"]}
        request_id = headers.get("x-request-id", str(uuid4()))
        settings = get_settings()

        request_id_token = request_id_context.set(request_id)
        model_profile_token = model_profile_context.set(settings.model_profile)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode("utf-8")))
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_context.reset(request_id_token)
            model_profile_context.reset(model_profile_token)


class RequestSizeLimitMiddleware:
    """Reject request bodies that exceed the configured content-length limit."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Short-circuit oversized requests before the app reads the body."""

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.decode("latin-1"): value.decode("latin-1") for key, value in scope["headers"]}
        content_length_value = headers.get("content-length")
        if content_length_value is not None:
            max_bytes = get_settings().request_max_body_bytes
            content_length = int(content_length_value)
            if content_length > max_bytes:
                envelope = ErrorEnvelope(
                    error=ErrorDetails(
                        message=f"Request body exceeds the configured limit of {max_bytes} bytes.",
                        type="invalid_request_error",
                        code="request_too_large",
                        param=None,
                        request_id=headers.get("x-request-id", request_id_context.get()),
                    )
                )
                response = JSONResponse(status_code=413, content=envelope.model_dump())
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


class RequestMetricsMiddleware:
    """Capture Prometheus metrics and structured access logs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Measure latency and status codes for each HTTP request."""

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        started_at = perf_counter()
        status_code = 500

        async def send_with_metrics(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_with_metrics)
        finally:
            latency = perf_counter() - started_at
            REQUEST_COUNT.labels(method=request.method, path=request.url.path, status_code=str(status_code)).inc()
            REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(latency)
            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_seconds": round(latency, 6),
                },
            )
