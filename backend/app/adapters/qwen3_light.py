"""Qwen 3 lightweight adapter."""

from __future__ import annotations

from app.adapters.base import BaseModelAdapter, ModelProfile
from app.models.common import ReasoningConfig
from app.models.upstream import ChatTemplateKwargs, VllmExtraBody


class Qwen3LightAdapter(BaseModelAdapter):
    """Adapter for `Qwen/Qwen3-4B`."""

    profile = ModelProfile(
        key="qwen3-light",
        public_model_id="Qwen/Qwen3-4B",
        hf_model_id="Qwen/Qwen3-4B",
        reasoning_parser="qwen3",
        owned_by="Qwen",
        default_reasoning_enabled=False,
        max_output_tokens=4096,
    )

    @property
    def supports_reasoning(self) -> bool:
        """Qwen reasoning is not exposed as a stable normalized contract on this runtime."""

        return False

    @property
    def supports_responses(self) -> bool:
        """Qwen Responses output is not reliable enough on the current stable runtime."""

        return False

    def build_extra_body(self, reasoning: ReasoningConfig | None) -> VllmExtraBody | None:
        """Toggle Qwen thinking mode explicitly so normal mode remains the default."""

        enable_thinking = False if reasoning is None else bool(reasoning.enabled)
        return VllmExtraBody(chat_template_kwargs=ChatTemplateKwargs(enable_thinking=enable_thinking))
