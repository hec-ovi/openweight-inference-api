"""Business logic for proxying gateway requests to vLLM."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.adapters.base import BaseModelAdapter
from app.core.config import Settings
from app.core.errors import UpstreamServiceError
from app.core.types import JsonObject
from app.models.chat import ChatCompletionsRequest, ChatCompletionsResponse
from app.models.models_api import ModelListResponse
from app.models.responses import ResponsesRequest, ResponsesResponse
from app.services.responses_normalizer import normalize_responses_payload, normalize_responses_sse
from app.services.vllm_client import VllmClient


async def list_models(adapter: BaseModelAdapter) -> ModelListResponse:
    """Return the active model card."""

    return ModelListResponse(data=[adapter.build_model_card()])


async def create_chat_completion(
    request: ChatCompletionsRequest,
    adapter: BaseModelAdapter,
    client: VllmClient,
) -> ChatCompletionsResponse:
    """Proxy a non-streaming chat completion request."""

    try:
        payload = adapter.build_chat_request(request)
        data = await client.post_json("/v1/chat/completions", payload)
    except httpx.HTTPStatusError as exc:
        raise UpstreamServiceError(_extract_upstream_message(exc)) from exc
    return ChatCompletionsResponse.model_validate(data)


async def create_response(
    request: ResponsesRequest,
    adapter: BaseModelAdapter,
    client: VllmClient,
) -> ResponsesResponse:
    """Proxy a non-streaming responses request."""

    try:
        payload = adapter.build_responses_request(request)
        data = await client.post_json("/v1/responses", payload)
    except httpx.HTTPStatusError as exc:
        raise UpstreamServiceError(_extract_upstream_message(exc)) from exc
    data = normalize_responses_payload(data, payload.reasoning)
    return ResponsesResponse.model_validate(data)


async def stream_chat_completion(
    request: ChatCompletionsRequest,
    adapter: BaseModelAdapter,
    client: VllmClient,
    settings: Settings,
) -> AsyncIterator[bytes]:
    """Proxy an upstream chat completion SSE stream."""

    payload = adapter.build_chat_request(request)
    try:
        async with client.stream("/v1/chat/completions", payload, "chat_completions", settings.model_profile) as response:
            if response.status_code >= 400:
                raise UpstreamServiceError(await _extract_stream_error_message(response))
            async for chunk in response.aiter_bytes():
                if chunk:
                    yield chunk
    except httpx.HTTPError as exc:
        raise UpstreamServiceError(str(exc)) from exc


async def stream_response(
    request: ResponsesRequest,
    adapter: BaseModelAdapter,
    client: VllmClient,
    settings: Settings,
) -> AsyncIterator[bytes]:
    """Proxy an upstream responses SSE stream."""

    payload = adapter.build_responses_request(request)
    try:
        async with client.stream("/v1/responses", payload, "responses", settings.model_profile) as response:
            if response.status_code >= 400:
                raise UpstreamServiceError(await _extract_stream_error_message(response))
            async for chunk in normalize_responses_sse(response.aiter_bytes(), payload.reasoning):
                if chunk:
                    yield chunk
    except httpx.HTTPError as exc:
        raise UpstreamServiceError(str(exc)) from exc


def _extract_upstream_message(exc: httpx.HTTPStatusError) -> str:
    """Extract a usable message from an upstream error payload."""

    response = exc.response
    try:
        payload: JsonObject = response.json()
    except ValueError:
        return f"Upstream vLLM request failed with status {response.status_code}."

    error_payload = payload.get("error")
    if isinstance(error_payload, dict):
        message = error_payload.get("message")
        if isinstance(message, str):
            return message
    return f"Upstream vLLM request failed with status {response.status_code}."


async def _extract_stream_error_message(response: httpx.Response) -> str:
    """Extract an error message from a failed streaming request."""

    body = await response.aread()
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return f"Upstream vLLM streaming request failed with status {response.status_code}."

    error_payload = payload.get("error")
    if isinstance(error_payload, dict):
        message = error_payload.get("message")
        if isinstance(message, str):
            return message
    return f"Upstream vLLM streaming request failed with status {response.status_code}."
