"""Base adapter definitions for model-family isolation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import Field

from app.core.errors import ModelSelectionError, ReasoningNotSupportedError
from app.models.chat import ChatCompletionsRequest
from app.models.common import ReasoningConfig, StrictModel
from app.models.models_api import ModelCapabilities, ModelCard
from app.models.responses import ResponsesRequest
from app.models.upstream import UpstreamChatCompletionsRequest, UpstreamResponsesRequest, VllmExtraBody


class ModelProfile(StrictModel):
    """Static profile metadata for a supported model family."""

    key: Literal["qwen3-light", "deepseek-r1-distill", "gpt-oss"] = Field(description="Internal profile key.")
    public_model_id: str = Field(description="Public model identifier exposed by the gateway and vLLM.")
    hf_model_id: str = Field(description="Hugging Face model ID used for downloads.")
    family: str = Field(description="Internal model family name.")
    reasoning_parser: str | None = Field(default=None, description="vLLM reasoning parser name.")
    description: str = Field(description="Profile description.")
    owned_by: str = Field(description="Owning organization.")
    default_reasoning_enabled: bool = Field(description="Whether reasoning is enabled by default.")
    vllm_launch_args: tuple[str, ...] = Field(description="Profile-specific vLLM serve flags.")
    max_context_tokens: int = Field(description="Safe default context length.")
    max_output_tokens: int = Field(description="Safe default output length.")


class BaseModelAdapter(ABC):
    """Base adapter for translating stable API requests into profile-specific vLLM calls."""

    profile: ModelProfile

    def assert_model(self, requested_model: str | None) -> str:
        """Ensure the request targets the active model."""

        active_model = self.profile.public_model_id
        if requested_model is None:
            return active_model
        if requested_model != active_model:
            raise ModelSelectionError(requested_model=requested_model, active_model=active_model)
        return active_model

    def resolve_reasoning(self, requested: ReasoningConfig | None) -> ReasoningConfig | None:
        """Normalize reasoning controls for the active profile."""

        if requested is None:
            if not self.profile.default_reasoning_enabled:
                return None
            return ReasoningConfig(enabled=True)

        if requested.enabled is False and requested.include:
            return ReasoningConfig(enabled=False, effort=requested.effort, include=False)

        if requested.enabled is None:
            return ReasoningConfig(
                enabled=self.profile.default_reasoning_enabled,
                effort=requested.effort,
                include=requested.include,
            )

        return requested

    def build_model_card(self) -> ModelCard:
        """Expose the active model as an OpenAI-style model card."""

        return ModelCard(
            id=self.profile.public_model_id,
            owned_by=self.profile.owned_by,
            root=self.profile.public_model_id,
            capabilities=ModelCapabilities(
                responses=True,
                chat_completions=True,
                streaming=True,
                reasoning=self.supports_reasoning,
            ),
            profile=self.profile.key,
            hf_model_id=self.profile.hf_model_id,
            reasoning_parser=self.profile.reasoning_parser,
        )

    @property
    @abstractmethod
    def supports_reasoning(self) -> bool:
        """Return whether the profile exposes normalized reasoning controls."""

    @abstractmethod
    def build_extra_body(self, reasoning: ReasoningConfig | None) -> VllmExtraBody | None:
        """Build vLLM-specific request hints for this profile."""

    def build_chat_request(self, request: ChatCompletionsRequest) -> UpstreamChatCompletionsRequest:
        """Translate a public chat request into a vLLM-compatible payload."""

        model = self.assert_model(request.model)
        reasoning = self.resolve_reasoning(request.reasoning)
        if reasoning is not None and not self.supports_reasoning and reasoning.enabled:
            raise ReasoningNotSupportedError(self.profile.key)

        return UpstreamChatCompletionsRequest(
            model=model,
            messages=request.messages,
            stream=request.stream,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            reasoning=reasoning,
            extra_body=self.build_extra_body(reasoning),
        )

    def build_responses_request(self, request: ResponsesRequest) -> UpstreamResponsesRequest:
        """Translate a public responses request into a vLLM-compatible payload."""

        model = self.assert_model(request.model)
        reasoning = self.resolve_reasoning(request.reasoning)
        if reasoning is not None and not self.supports_reasoning and reasoning.enabled:
            raise ReasoningNotSupportedError(self.profile.key)

        return UpstreamResponsesRequest(
            model=model,
            input=request.input,
            stream=request.stream,
            temperature=request.temperature,
            top_p=request.top_p,
            max_output_tokens=request.max_output_tokens,
            reasoning=reasoning,
            extra_body=self.build_extra_body(reasoning),
        )
