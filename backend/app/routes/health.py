"""Health routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.adapters.registry import get_adapter
from app.core.config import Settings, get_settings
from app.models.health import HealthStatusResponse
from app.services.health import liveness, readiness
from app.services.vllm_client import VllmClient

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live(settings: Settings = Depends(get_settings)) -> HealthStatusResponse:
    """Return the liveness status of the gateway."""

    return await liveness(settings.model_profile)


@router.get("/health/ready")
async def ready(settings: Settings = Depends(get_settings)) -> HealthStatusResponse:
    """Return readiness for the gateway and the active model server."""

    adapter = get_adapter(settings.model_profile)
    payload = await readiness(settings.model_profile, adapter, VllmClient(settings))
    if payload.status != "ready":
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload
