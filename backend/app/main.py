"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.registry import get_adapter
from app.core.config import get_settings
from app.core.context import request_id_context
from app.core.errors import GatewayError, UpstreamServiceError, error_envelope
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, RequestMetricsMiddleware, RequestSizeLimitMiddleware
from app.models.errors import ErrorDetails, ErrorEnvelope
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.routes.metrics import router as metrics_router
from app.routes.models import router as models_router
from app.routes.responses import router as responses_router

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()
    configure_logging(settings.app_log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        summary="ROCm-first gateway for open-weight chat and reasoning models.",
        openapi_version="3.1.0",
    )

    app.add_middleware(RequestMetricsMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    app.include_router(health_router)
    app.include_router(models_router)
    app.include_router(chat_router)
    app.include_router(responses_router)
    app.include_router(metrics_router)

    @app.exception_handler(GatewayError)
    async def handle_gateway_error(_: Request, exc: GatewayError) -> JSONResponse:
        """Convert domain errors into stable JSON payloads."""

        return JSONResponse(status_code=exc.status_code, content=error_envelope(exc).model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Return structured request validation errors."""

        first_error = exc.errors()[0]
        envelope = ErrorEnvelope(
            error=ErrorDetails(
                message=first_error["msg"],
                type="invalid_request_error",
                code="validation_error",
                param=".".join(str(part) for part in first_error["loc"]),
                request_id=request_id_context.get(),
            )
        )
        return JSONResponse(status_code=422, content=envelope.model_dump())

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        """Normalize FastAPI HTTP errors."""

        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
        envelope = ErrorEnvelope(
            error=ErrorDetails(
                message=detail,
                type="invalid_request_error" if exc.status_code < 500 else "server_error",
                code="http_error",
                param=None,
                request_id=request_id_context.get(),
            )
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        """Guard against uncaught exceptions leaking internals."""

        return JSONResponse(
            status_code=500,
            content=error_envelope(UpstreamServiceError("The gateway encountered an unexpected error.", status_code=500)).model_dump(),
        )

    return app


app = create_app()
