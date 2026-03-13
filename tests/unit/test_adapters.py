"""Adapter behavior tests."""

from __future__ import annotations

import pytest

from app.adapters.deepseek_r1_distill import DeepSeekR1DistillAdapter
from app.adapters.gpt_oss import GptOssAdapter
from app.adapters.qwen3_light import Qwen3LightAdapter
from app.core.errors import EndpointNotSupportedError, ReasoningNotSupportedError
from app.models.chat import ChatCompletionsRequest, ChatMessage
from app.models.common import ReasoningConfig
from app.models.responses import ResponsesRequest


def test_qwen_disables_thinking_by_default() -> None:
    """Qwen should default to non-thinking mode."""

    adapter = Qwen3LightAdapter()
    payload = adapter.build_chat_request(
        ChatCompletionsRequest(
            model="Qwen/Qwen3-4B",
            messages=[ChatMessage(role="user", content="Hello")],
        )
    )
    assert payload.extra_body is not None
    assert payload.extra_body.chat_template_kwargs is not None
    assert payload.extra_body.chat_template_kwargs.enable_thinking is False


def test_qwen_rejects_normalized_reasoning_requests() -> None:
    """Qwen should not advertise normalized reasoning on the current stable runtime."""

    adapter = Qwen3LightAdapter()

    with pytest.raises(ReasoningNotSupportedError):
        adapter.build_chat_request(
            ChatCompletionsRequest(
                model="Qwen/Qwen3-4B",
                messages=[ChatMessage(role="user", content="Hello")],
                reasoning=ReasoningConfig(enabled=True, include=True),
            )
        )


def test_qwen_rejects_responses_endpoint() -> None:
    """Qwen should fail closed on Responses until the upstream runtime is clean."""

    adapter = Qwen3LightAdapter()

    with pytest.raises(EndpointNotSupportedError):
        adapter.build_responses_request(
            ResponsesRequest(
                model="Qwen/Qwen3-4B",
                input="Hello",
            )
        )


def test_deepseek_defaults_to_reasoning() -> None:
    """DeepSeek should opt into reasoning when not overridden."""

    adapter = DeepSeekR1DistillAdapter()
    payload = adapter.build_chat_request(
        ChatCompletionsRequest(
            model="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            messages=[ChatMessage(role="user", content="Hello")],
        )
    )
    assert payload.reasoning is not None
    assert payload.reasoning.enabled is True


def test_gpt_oss_can_disable_reasoning_output() -> None:
    """GPT-OSS should allow suppressing reasoning traces."""

    adapter = GptOssAdapter()
    payload = adapter.build_chat_request(
        ChatCompletionsRequest(
            model="openai/gpt-oss-20b",
            messages=[ChatMessage(role="user", content="Hello")],
            reasoning=ReasoningConfig(enabled=False, include=False),
        )
    )
    assert payload.extra_body is not None
    assert payload.extra_body.include_reasoning is False


def test_deepseek_adds_hidden_reasoning_headroom_when_plain_mode_is_requested() -> None:
    """Reasoning-native models need extra upstream budget even when reasoning is hidden."""

    adapter = DeepSeekR1DistillAdapter()
    payload = adapter.build_chat_request(
        ChatCompletionsRequest(
            model="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            messages=[ChatMessage(role="user", content="Hello")],
            max_tokens=40,
            reasoning=ReasoningConfig(enabled=False, include=False),
        )
    )

    assert payload.max_tokens == 104


def test_gpt_oss_adds_hidden_reasoning_headroom_for_responses_plain_mode() -> None:
    """Responses requests should receive the same hidden-reasoning headroom."""

    adapter = GptOssAdapter()
    payload = adapter.build_responses_request(
        ResponsesRequest(
            model="openai/gpt-oss-20b",
            input="Hello",
            max_output_tokens=40,
            reasoning=ReasoningConfig(enabled=False, include=False),
        )
    )

    assert payload.max_output_tokens == 104
