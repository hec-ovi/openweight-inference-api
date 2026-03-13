"""Base adapter definitions for model-family isolation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import Field

from app.core.errors import EndpointNotSupportedError, ModelSelectionError, ReasoningNotSupportedError
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
    reasoning_parser: str | None = Field(default=None, description="vLLM reasoning parser name.")
    owned_by: str = Field(description="Owning organization.")
    default_reasoning_enabled: bool = Field(description="Whether reasoning is enabled by default.")
    max_output_tokens: int = Field(description="Safe default output length.")


class BaseModelAdapter(ABC):
    """Base adapter for translating stable API requests into profile-specific vLLM calls."""

    profile: ModelProfile
    _HIDDEN_REASONING_TOKEN_HEADROOM = 64

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
                responses=self.supports_responses,
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

    @property
    def supports_responses(self) -> bool:
        """Return whether the profile exposes `/v1/responses` as a stable contract."""

        return True

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
            max_tokens=self._resolve_upstream_output_limit(request.max_tokens, reasoning),
            reasoning=reasoning,
            extra_body=self.build_extra_body(reasoning),
        )

    def build_responses_request(self, request: ResponsesRequest) -> UpstreamResponsesRequest:
        """Translate a public responses request into a vLLM-compatible payload."""

        if not self.supports_responses:
            raise EndpointNotSupportedError(self.profile.key, "/v1/responses")

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
            max_output_tokens=self._resolve_upstream_output_limit(request.max_output_tokens, reasoning),
            reasoning=reasoning,
            extra_body=self.build_extra_body(reasoning),
        )

    def _resolve_upstream_output_limit(self, requested_limit: int | None, reasoning: ReasoningConfig | None) -> int | None:
        """Add headroom when hidden reasoning still consumes upstream output tokens."""

        if requested_limit is None:
            return None

        if not self.profile.default_reasoning_enabled:
            return requested_limit

        if reasoning is None or reasoning.enabled is not False or reasoning.include is not False:
            return requested_limit

        return min(
            self.profile.max_output_tokens,
            requested_limit + max(self._HIDDEN_REASONING_TOKEN_HEADROOM, requested_limit),
        )
