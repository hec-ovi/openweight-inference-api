"""Typed HTTP client for the upstream vLLM server."""

from __future__ import annotations

from contextlib import asynccontextmanager
from time import perf_counter
from typing import AsyncIterator

import httpx

from app.core.config import Settings
from app.core.metrics import STREAM_DURATION, UPSTREAM_FAILURES
from app.core.types import JsonObject
from app.models.upstream import UpstreamChatCompletionsRequest, UpstreamResponsesRequest


class VllmClient:
    """HTTP wrapper for vLLM OpenAI-compatible endpoints."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def post_json(self, path: str, payload: UpstreamChatCompletionsRequest | UpstreamResponsesRequest) -> JsonObject:
        """Send a JSON request to vLLM and return the JSON response."""

        timeout = httpx.Timeout(timeout=self._settings.vllm_request_timeout_seconds)
        async with httpx.AsyncClient(base_url=self._settings.vllm_base_url, timeout=timeout) as client:
            response = await client.post(path, json=payload.model_dump(exclude_none=True))
            if response.status_code >= 400:
                UPSTREAM_FAILURES.labels(endpoint=path, reason=str(response.status_code)).inc()
                raise httpx.HTTPStatusError("Upstream request failed.", request=response.request, response=response)
            return response.json()

    async def get_json(self, path: str) -> JsonObject:
        """Fetch JSON from vLLM."""

        timeout = httpx.Timeout(timeout=self._settings.vllm_request_timeout_seconds)
        async with httpx.AsyncClient(base_url=self._settings.vllm_base_url, timeout=timeout) as client:
            response = await client.get(path)
            if response.status_code >= 400:
                UPSTREAM_FAILURES.labels(endpoint=path, reason=str(response.status_code)).inc()
                raise httpx.HTTPStatusError("Upstream request failed.", request=response.request, response=response)
            return response.json()

    async def check_health(self) -> bool:
        """Return whether vLLM is alive."""

        timeout = httpx.Timeout(timeout=min(self._settings.vllm_request_timeout_seconds, 10.0))
        async with httpx.AsyncClient(base_url=self._settings.vllm_base_url, timeout=timeout) as client:
            response = await client.get(self._settings.vllm_health_path)
            return response.status_code < 400

    @asynccontextmanager
    async def stream(
        self,
        path: str,
        payload: UpstreamChatCompletionsRequest | UpstreamResponsesRequest,
        endpoint: str,
        model_profile: str,
    ) -> AsyncIterator[httpx.Response]:
        """Open a streaming connection to vLLM."""

        timeout = httpx.Timeout(connect=10.0, read=self._settings.vllm_stream_timeout_seconds, write=30.0, pool=30.0)
        started_at = perf_counter()
        async with httpx.AsyncClient(base_url=self._settings.vllm_base_url, timeout=timeout) as client:
            async with client.stream("POST", path, json=payload.model_dump(exclude_none=True)) as response:
                try:
                    yield response
                finally:
                    STREAM_DURATION.labels(endpoint=endpoint, model_profile=model_profile).observe(perf_counter() - started_at)

