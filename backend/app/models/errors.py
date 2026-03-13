"""Structured error response schemas."""

from __future__ import annotations

from pydantic import Field

from app.models.common import StrictModel


class ErrorDetails(StrictModel):
    """OpenAI-style error payload."""

    message: str = Field(description="Human-readable error message.")
    type: str = Field(description="Stable error type identifier.")
    code: str = Field(description="Stable machine-readable error code.")
    param: str | None = Field(default=None, description="Related parameter, when known.")
    request_id: str = Field(description="Gateway request identifier.")


class ErrorEnvelope(StrictModel):
    """Error envelope returned by the gateway."""

    error: ErrorDetails = Field(description="Error details.")

