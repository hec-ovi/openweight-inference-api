"""Shared schemas used by multiple endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model that rejects undeclared fields."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FlexibleModel(BaseModel):
    """Base model that accepts upstream-compatible extension fields."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


ReasoningEffort = Literal["low", "medium", "high"]


class ReasoningConfig(StrictModel):
    """Normalized reasoning controls exposed by the public API."""

    enabled: bool | None = Field(default=None, description="Enable model reasoning when supported.")
    effort: ReasoningEffort = Field(default="medium", description="Normalized reasoning effort level.")
    include: bool = Field(default=True, description="Include reasoning traces when the model and endpoint support it.")


class TokenUsage(FlexibleModel):
    """Token usage details from the upstream model server."""

    prompt_tokens: int | None = Field(default=None, description="Prompt or input token count.")
    completion_tokens: int | None = Field(default=None, description="Completion or output token count.")
    total_tokens: int | None = Field(default=None, description="Total tokens used.")
    reasoning_tokens: int | None = Field(default=None, description="Reasoning tokens when available.")

