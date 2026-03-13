"""Model adapter registry."""

from __future__ import annotations

from app.adapters.base import BaseModelAdapter
from app.adapters.deepseek_r1_distill import DeepSeekR1DistillAdapter
from app.adapters.gpt_oss import GptOssAdapter
from app.adapters.qwen35_light import Qwen35LightAdapter

ADAPTERS: dict[str, BaseModelAdapter] = {
    "qwen3.5-light": Qwen35LightAdapter(),
    "deepseek-r1-distill": DeepSeekR1DistillAdapter(),
    "gpt-oss": GptOssAdapter(),
}


def get_adapter(profile_key: str) -> BaseModelAdapter:
    """Return the adapter for the configured profile."""

    return ADAPTERS[profile_key]

