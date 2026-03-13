"""Responses API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.adapters.registry import get_adapter
from app.core.auth import require_bearer_token
from app.core.config import Settings, get_settings
from app.models.responses import ResponsesRequest, ResponsesResponse
from app.services.gateway import create_response, stream_response
from app.services.vllm_client import VllmClient

router = APIRouter(tags=["responses"])


@router.post("/v1/responses")
async def responses(
    request: ResponsesRequest,
    _: Annotated[str, Depends(require_bearer_token)],
    settings: Settings = Depends(get_settings),
) -> ResponsesResponse:
    """Return a response object or stream it over SSE."""

    adapter = get_adapter(settings.model_profile)
    client = VllmClient(settings)

    if request.stream:
        return StreamingResponse(
            stream_response(request, adapter, client, settings),
            media_type="text/event-stream",
            headers={"cache-control": "no-cache"},
        )

    return await create_response(request, adapter, client)

