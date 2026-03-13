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
        family="qwen3",
        reasoning_parser="qwen3",
        description="Lightweight Qwen 3 profile with thinking disabled by default.",
        owned_by="Qwen",
        default_reasoning_enabled=False,
        vllm_launch_args=(
            "--reasoning-parser",
            "qwen3",
            "--max-model-len",
            "32768",
        ),
        max_context_tokens=32768,
        max_output_tokens=4096,
    )

    @property
    def supports_reasoning(self) -> bool:
        """Qwen supports explicit thinking mode."""

        return True

    def build_extra_body(self, reasoning: ReasoningConfig | None) -> VllmExtraBody | None:
        """Toggle Qwen thinking mode explicitly so normal mode remains the default."""

        enable_thinking = False if reasoning is None else bool(reasoning.enabled)
        return VllmExtraBody(chat_template_kwargs=ChatTemplateKwargs(enable_thinking=enable_thinking))
