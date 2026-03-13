"""Health and readiness checks."""

from __future__ import annotations

import httpx

from app.adapters.base import BaseModelAdapter
from app.core.metrics import READINESS_STATUS
from app.models.health import HealthStatusResponse
from app.services.vllm_client import VllmClient


async def liveness(model_profile: str) -> HealthStatusResponse:
    """Return a simple liveness payload."""

    return HealthStatusResponse(status="ok", model_profile=model_profile, upstream="unknown")


async def readiness(model_profile: str, adapter: BaseModelAdapter, client: VllmClient) -> HealthStatusResponse:
    """Verify that vLLM is healthy and serving the configured model."""

    try:
        upstream_alive = await client.check_health()
        model_payload = await client.get_json("/v1/models")
    except httpx.HTTPError:
        READINESS_STATUS.set(0)
        return HealthStatusResponse(status="not_ready", model_profile=model_profile, upstream="unreachable")

    active_models = model_payload.get("data")
    is_active = False
    if isinstance(active_models, list):
        is_active = any(
            isinstance(model_item, dict) and model_item.get("id") == adapter.profile.public_model_id
            for model_item in active_models
        )

    ready = upstream_alive and is_active
    READINESS_STATUS.set(1 if ready else 0)
    return HealthStatusResponse(
        status="ready" if ready else "not_ready",
        model_profile=model_profile,
        upstream="ready" if ready else "model_not_loaded",
    )

