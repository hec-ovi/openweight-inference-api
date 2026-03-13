"""DeepSeek R1 Distill adapter."""

from __future__ import annotations

from app.adapters.base import BaseModelAdapter, ModelProfile
from app.models.common import ReasoningConfig
from app.models.upstream import VllmExtraBody


class DeepSeekR1DistillAdapter(BaseModelAdapter):
    """Adapter for `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`."""

    profile = ModelProfile(
        key="deepseek-r1-distill",
        public_model_id="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        hf_model_id="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        family="deepseek-r1-distill",
        reasoning_parser="deepseek_r1",
        description="Reasoning-capable DeepSeek distill profile.",
        owned_by="deepseek-ai",
        default_reasoning_enabled=True,
        vllm_launch_args=(
            "--reasoning-parser",
            "deepseek_r1",
            "--max-model-len",
            "32768",
        ),
        max_context_tokens=32768,
        max_output_tokens=8192,
    )

    @property
    def supports_reasoning(self) -> bool:
        """DeepSeek distill supports reasoning output."""

        return True

    def build_extra_body(self, reasoning: ReasoningConfig | None) -> VllmExtraBody | None:
        """Control whether reasoning content should be included in responses."""

        if reasoning is None:
            return VllmExtraBody(include_reasoning=True)
        return VllmExtraBody(include_reasoning=reasoning.include)

