"""Domain-specific exceptions and payload helpers."""

from __future__ import annotations

from starlette import status

from app.core.context import request_id_context
from app.models.errors import ErrorDetails, ErrorEnvelope


class GatewayError(Exception):
    """Base exception for gateway failures."""

    def __init__(self, status_code: int, code: str, message: str, error_type: str, param: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.error_type = error_type
        self.param = param


class AuthenticationError(GatewayError):
    """Bearer authentication failed."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_api_key",
            message="A valid bearer token is required for this endpoint.",
            error_type="authentication_error",
        )


class ModelSelectionError(GatewayError):
    """The request targeted a model that is not active."""

    def __init__(self, requested_model: str, active_model: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_model",
            message=f"Requested model '{requested_model}' does not match the active deployment model '{active_model}'.",
            error_type="invalid_request_error",
            param="model",
        )


class ReasoningNotSupportedError(GatewayError):
    """The active model profile does not support the requested reasoning mode."""

    def __init__(self, model_profile: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="unsupported_reasoning",
            message=f"Model profile '{model_profile}' does not support the requested reasoning mode.",
            error_type="invalid_request_error",
            param="reasoning",
        )


class UpstreamServiceError(GatewayError):
    """vLLM returned an error or became unavailable."""

    def __init__(self, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY) -> None:
        super().__init__(
            status_code=status_code,
            code="upstream_error",
            message=message,
            error_type="server_error",
        )


def error_envelope(error: GatewayError) -> ErrorEnvelope:
    """Build the serialized error envelope."""

    return ErrorEnvelope(
        error=ErrorDetails(
            message=error.message,
            type=error.error_type,
            code=error.code,
            param=error.param,
            request_id=request_id_context.get(),
        )
    )

