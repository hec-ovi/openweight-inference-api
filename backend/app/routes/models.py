"""Model routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.adapters.registry import get_adapter
from app.core.auth import require_bearer_token
from app.core.config import Settings, get_settings
from app.models.models_api import ModelListResponse
from app.services.gateway import list_models

router = APIRouter(tags=["models"])


@router.get("/v1/models")
async def models(
    _: Annotated[str, Depends(require_bearer_token)],
    settings: Settings = Depends(get_settings),
) -> ModelListResponse:
    """Return the active served model."""

    return await list_models(get_adapter(settings.model_profile))

