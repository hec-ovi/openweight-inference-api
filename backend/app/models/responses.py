"""Responses API request and response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.models.common import FlexibleModel, ReasoningConfig, StrictModel, TokenUsage


ResponseRole = Literal["system", "user", "assistant"]


class ResponseInputTextPart(StrictModel):
    """Text part for multi-part input items."""

    type: Literal["input_text"] = Field(default="input_text", description="Input content type.")
    text: str = Field(description="Input text.")


class ResponseInputMessage(StrictModel):
    """Message item accepted by the Responses API."""

    role: ResponseRole = Field(description="Input role.")
    content: str | list[ResponseInputTextPart] = Field(description="Input content.")


class ResponsesRequest(StrictModel):
    """Request for `POST /v1/responses`."""

    model: str | None = Field(default=None, description="Requested model. Omit to target the active deployment model.")
    input: str | list[ResponseInputMessage] = Field(description="Input payload.")
    stream: bool = Field(default=False, description="Stream the response over SSE.")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Sampling temperature.")
    top_p: float | None = Field(default=None, gt=0.0, le=1.0, description="Nucleus sampling value.")
    max_output_tokens: int | None = Field(default=None, gt=0, description="Maximum number of output tokens.")
    reasoning: ReasoningConfig | None = Field(default=None, description="Normalized reasoning controls.")


class ResponseOutputText(FlexibleModel):
    """Generated text content item."""

    type: str = Field(default="output_text", description="Output item type.")
    text: str | None = Field(default=None, description="Generated text.")


class ResponseOutputMessage(FlexibleModel):
    """Assistant output item."""

    type: str = Field(default="message", description="Output object type.")
    role: str = Field(default="assistant", description="Output role.")
    content: list[ResponseOutputText] = Field(default_factory=list, description="Generated content parts.")


class ResponsesResponse(FlexibleModel):
    """OpenAI-style response object."""

    id: str = Field(description="Unique response identifier.")
    object: str = Field(default="response", description="Object type.")
    created_at: int | None = Field(default=None, description="Unix timestamp when created.")
    model: str = Field(description="Served model identifier.")
    status: str | None = Field(default=None, description="Current response status.")
    output: list[ResponseOutputMessage] = Field(default_factory=list, description="Output items.")
    usage: TokenUsage | None = Field(default=None, description="Usage statistics.")

