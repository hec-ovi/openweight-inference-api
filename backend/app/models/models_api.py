"""Model listing schemas."""

from __future__ import annotations

from pydantic import Field

from app.models.common import FlexibleModel, StrictModel


class ModelCapabilities(StrictModel):
    """Capability flags exposed for the active model profile."""

    responses: bool = Field(description="Supports the Responses API.")
    chat_completions: bool = Field(description="Supports Chat Completions compatibility.")
    streaming: bool = Field(description="Supports streaming output.")
    reasoning: bool = Field(description="Supports normalized reasoning controls.")


class ModelCard(FlexibleModel):
    """OpenAI-style model card."""

    id: str = Field(description="Public model identifier exposed by the gateway.")
    object: str = Field(default="model", description="OpenAI-style object type.")
    owned_by: str = Field(description="Owning organization for the model family.")
    root: str = Field(description="Root model identifier.")
    capabilities: ModelCapabilities = Field(description="Gateway-level model capabilities.")
    profile: str = Field(description="Internal active model profile key.")
    hf_model_id: str = Field(description="Backing Hugging Face model ID.")
    reasoning_parser: str | None = Field(default=None, description="Configured vLLM reasoning parser.")


class ModelListResponse(StrictModel):
    """Response for `GET /v1/models`."""

    object: str = Field(default="list", description="Collection object type.")
    data: list[ModelCard] = Field(description="Active model list.")

