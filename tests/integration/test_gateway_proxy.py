"""Integration tests for JSON proxying."""

from __future__ import annotations

import asyncio

from app.models.chat import ChatCompletionsRequest, ChatMessage
from app.routes.chat import chat_completions
from app.routes.models import models
from app.services.vllm_client import VllmClient


def test_chat_proxy_sends_qwen_thinking_flag(settings, monkeypatch) -> None:
    """The gateway should send Qwen's thinking toggle explicitly."""

    captured: dict[str, object] = {}

    async def fake_post_json(self, path, payload):
        captured["path"] = path
        captured["payload"] = payload
        return {
            "id": "chatcmpl_123",
            "object": "chat.completion",
            "created": 1,
            "model": "Qwen/Qwen3.5-4B",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "ready"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        }

    monkeypatch.setattr(VllmClient, "post_json", fake_post_json)

    response = asyncio.run(
        chat_completions(
            ChatCompletionsRequest(
                model="Qwen/Qwen3.5-4B",
                messages=[ChatMessage(role="user", content="Say hello")],
            ),
            "test-token",
            settings,
        )
    )

    assert captured["path"] == "/v1/chat/completions"
    upstream_payload = captured["payload"]
    assert upstream_payload.extra_body.chat_template_kwargs.enable_thinking is False
    assert response.choices[0].message.content == "ready"


def test_models_endpoint_returns_active_profile(settings) -> None:
    """The gateway should expose only the active deployment model."""

    payload = asyncio.run(models("test-token", settings))
    assert payload.data[0].id == "Qwen/Qwen3.5-4B"
