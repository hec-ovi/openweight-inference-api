"""Adapter behavior tests."""

from __future__ import annotations

from app.adapters.deepseek_r1_distill import DeepSeekR1DistillAdapter
from app.adapters.gpt_oss import GptOssAdapter
from app.adapters.qwen35_light import Qwen35LightAdapter
from app.models.chat import ChatCompletionsRequest, ChatMessage
from app.models.common import ReasoningConfig


def test_qwen_disables_thinking_by_default() -> None:
    """Qwen should default to non-thinking mode."""

    adapter = Qwen35LightAdapter()
    payload = adapter.build_chat_request(
        ChatCompletionsRequest(
            model="Qwen/Qwen3.5-4B",
            messages=[ChatMessage(role="user", content="Hello")],
        )
    )
    assert payload.extra_body is not None
    assert payload.extra_body.chat_template_kwargs is not None
    assert payload.extra_body.chat_template_kwargs.enable_thinking is False


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

