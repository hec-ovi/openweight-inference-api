"""GPT-OSS Harmony-specific adapter."""

from __future__ import annotations

from app.adapters.base import BaseModelAdapter, ModelProfile
from app.models.common import ReasoningConfig
from app.models.upstream import VllmExtraBody


class GptOssAdapter(BaseModelAdapter):
    """Adapter for the OpenAI GPT-OSS family via the Harmony protocol path."""

    profile = ModelProfile(
        key="gpt-oss",
        public_model_id="openai/gpt-oss-20b",
        hf_model_id="openai/gpt-oss-20b",
        family="gpt-oss-harmony",
        reasoning_parser="gptoss",
        description="Harmony-based OpenAI GPT-OSS reasoning profile.",
        owned_by="openai",
        default_reasoning_enabled=True,
        vllm_launch_args=(
            "--reasoning-parser",
            "gptoss",
            "--max-model-len",
            "32768",
        ),
        max_context_tokens=32768,
        max_output_tokens=8192,
    )

    @property
    def supports_reasoning(self) -> bool:
        """GPT-OSS exposes explicit reasoning controls."""

        return True

    def build_extra_body(self, reasoning: ReasoningConfig | None) -> VllmExtraBody | None:
        """Keep Harmony-specific reasoning output explicit."""

        if reasoning is None:
            return VllmExtraBody(include_reasoning=True)
        return VllmExtraBody(include_reasoning=reasoning.include if reasoning.enabled is not False else False)

