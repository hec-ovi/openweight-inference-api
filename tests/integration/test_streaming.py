"""Streaming proxy tests."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi.responses import StreamingResponse

from app.models.responses import ResponsesRequest
from app.routes.responses import responses
from app.services.vllm_client import VllmClient


class DummyStreamResponse:
    """Minimal response wrapper for streaming tests."""

    status_code = 200

    async def aiter_bytes(self):
        """Yield fake SSE bytes."""

        yield b"data: {\"type\":\"response.output_text.delta\",\"delta\":\"hello\"}\n\ndata: [DONE]\n\n"

    async def aread(self) -> bytes:
        """Return the buffered body when asked for errors."""

        return b""


async def _collect_stream(response: StreamingResponse) -> str:
    """Consume a FastAPI streaming response."""

    chunks: list[bytes] = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8")


def test_responses_stream_passthrough(settings, monkeypatch) -> None:
    """The gateway should proxy upstream SSE bytes unchanged."""

    @asynccontextmanager
    async def fake_stream(self, path, payload, endpoint, model_profile):
        yield DummyStreamResponse()

    monkeypatch.setattr(VllmClient, "stream", fake_stream)

    response = asyncio.run(
        responses(
            ResponsesRequest(
                model="Qwen/Qwen3-4B",
                input="stream",
                stream=True,
            ),
            "test-token",
            settings,
        )
    )

    assert isinstance(response, StreamingResponse)
    assert response.media_type == "text/event-stream"
    assert "response.output_text.delta" in asyncio.run(_collect_stream(response))
