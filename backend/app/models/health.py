"""Health check schemas."""

from __future__ import annotations

from pydantic import Field

from app.models.common import StrictModel


class HealthStatusResponse(StrictModel):
    """Liveness or readiness payload."""

    status: str = Field(description="Current health state.")
    model_profile: str = Field(description="Configured model profile.")
    upstream: str = Field(description="Current upstream health verdict.")

