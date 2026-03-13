"""Typed upstream payload schemas."""

from __future__ import annotations

from pydantic import Field

from app.models.chat import ChatMessage
from app.models.common import ReasoningConfig, StrictModel
from app.models.responses import ResponseInputMessage


class ChatTemplateKwargs(StrictModel):
    """vLLM chat template keyword arguments."""

    enable_thinking: bool | None = Field(default=None, description="Enable or disable template-side thinking mode.")


class VllmExtraBody(StrictModel):
    """vLLM OpenAI-compatible extra request body."""

    chat_template_kwargs: ChatTemplateKwargs | None = Field(default=None, description="Template-specific options.")
    include_reasoning: bool | None = Field(default=None, description="Request explicit reasoning output when supported.")


class UpstreamChatCompletionsRequest(StrictModel):
    """Normalized chat request sent to vLLM."""

    model: str = Field(description="Served model identifier.")
    messages: list[ChatMessage] = Field(description="Chat messages.")
    stream: bool = Field(default=False, description="Enable streaming.")
    temperature: float | None = Field(default=None, description="Sampling temperature.")
    top_p: float | None = Field(default=None, description="Nucleus sampling.")
    max_tokens: int | None = Field(default=None, description="Maximum output tokens.")
    reasoning: ReasoningConfig | None = Field(default=None, description="Normalized reasoning controls.")
    extra_body: VllmExtraBody | None = Field(default=None, description="vLLM compatibility extensions.")


class UpstreamResponsesRequest(StrictModel):
    """Normalized Responses API request sent to vLLM."""

    model: str = Field(description="Served model identifier.")
    input: str | list[ResponseInputMessage] = Field(description="Input payload.")
    stream: bool = Field(default=False, description="Enable streaming.")
    temperature: float | None = Field(default=None, description="Sampling temperature.")
    top_p: float | None = Field(default=None, description="Nucleus sampling.")
    max_output_tokens: int | None = Field(default=None, description="Maximum output tokens.")
    reasoning: ReasoningConfig | None = Field(default=None, description="Normalized reasoning controls.")
    extra_body: VllmExtraBody | None = Field(default=None, description="vLLM compatibility extensions.")

