"""Chat Completions routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.adapters.registry import get_adapter
from app.core.auth import require_bearer_token
from app.core.config import Settings, get_settings
from app.models.chat import ChatCompletionsRequest, ChatCompletionsResponse
from app.services.gateway import create_chat_completion, stream_chat_completion
from app.services.vllm_client import VllmClient

router = APIRouter(tags=["chat"])


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionsRequest,
    _: Annotated[str, Depends(require_bearer_token)],
    settings: Settings = Depends(get_settings),
) -> ChatCompletionsResponse:
    """Return a chat completion or stream it over SSE."""

    adapter = get_adapter(settings.model_profile)
    client = VllmClient(settings)

    if request.stream:
        return StreamingResponse(
            stream_chat_completion(request, adapter, client, settings),
            media_type="text/event-stream",
            headers={"cache-control": "no-cache"},
        )

    return await create_chat_completion(request, adapter, client)

