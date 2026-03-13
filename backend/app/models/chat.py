"""Chat Completions request and response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.models.common import FlexibleModel, ReasoningConfig, StrictModel, TokenUsage


ChatRole = Literal["system", "user", "assistant", "tool"]


class ChatMessage(StrictModel):
    """Single message in a chat conversation."""

    role: ChatRole = Field(description="Message role.")
    content: str = Field(description="Message content.")


class ChatCompletionsRequest(StrictModel):
    """Compatibility request for `POST /v1/chat/completions`."""

    model: str | None = Field(default=None, description="Requested model. Omit to target the active deployment model.")
    messages: list[ChatMessage] = Field(min_length=1, description="Conversation messages.")
    stream: bool = Field(default=False, description="Stream the response over SSE.")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Sampling temperature.")
    top_p: float | None = Field(default=None, gt=0.0, le=1.0, description="Nucleus sampling value.")
    max_tokens: int | None = Field(default=None, gt=0, description="Maximum number of output tokens.")
    reasoning: ReasoningConfig | None = Field(default=None, description="Normalized reasoning controls.")


class ChatCompletionResponseMessage(FlexibleModel):
    """Assistant message returned by the model."""

    role: str = Field(description="Message role.")
    content: str | None = Field(default=None, description="Assistant response content.")
    reasoning: str | None = Field(default=None, description="Reasoning text when returned by the upstream.")


class ChatCompletionChoice(FlexibleModel):
    """Single completion choice."""

    index: int = Field(description="Choice index.")
    message: ChatCompletionResponseMessage = Field(description="Assistant message.")
    finish_reason: str | None = Field(default=None, description="Reason for stopping generation.")


class ChatCompletionsResponse(FlexibleModel):
    """OpenAI-style chat completion response."""

    id: str = Field(description="Unique completion identifier.")
    object: str = Field(default="chat.completion", description="Object type.")
    created: int = Field(description="Unix timestamp when the completion was created.")
    model: str = Field(description="Served model identifier.")
    choices: list[ChatCompletionChoice] = Field(description="Completion choices.")
    usage: TokenUsage | None = Field(default=None, description="Usage statistics.")

