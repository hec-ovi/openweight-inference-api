"""Environment-backed configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _parse_csv(value: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Normalize comma-separated or list-like env values."""

    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(item.strip() for item in value if item.strip())
    return tuple(item.strip() for item in value.split(",") if item.strip())


class Settings(BaseSettings):
    """Application settings loaded from env or `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "OpenWeight Responses API"
    app_env: Literal["development", "staging", "production", "test"] = "production"
    app_log_level: str = "INFO"

    api_bearer_keys: Annotated[tuple[str, ...], NoDecode] = Field(default=(), alias="API_BEARER_KEYS")
    cors_allow_origins: Annotated[tuple[str, ...], NoDecode] = Field(
        default=("http://localhost:8000",),
        alias="CORS_ALLOW_ORIGINS",
    )
    request_max_body_bytes: int = Field(default=1_048_576, alias="REQUEST_MAX_BODY_BYTES", ge=1024)

    model_profile: Literal["qwen3-light", "deepseek-r1-distill", "gpt-oss"] = Field(
        default="gpt-oss",
        alias="MODEL_PROFILE",
    )

    vllm_base_url: str = Field(default="http://vllm:8000", alias="VLLM_BASE_URL")
    vllm_request_timeout_seconds: float = Field(default=120.0, alias="VLLM_REQUEST_TIMEOUT_SECONDS", gt=0)
    vllm_stream_timeout_seconds: float = Field(default=900.0, alias="VLLM_STREAM_TIMEOUT_SECONDS", gt=0)
    vllm_health_path: str = Field(default="/health", alias="VLLM_HEALTH_PATH")

    @field_validator("api_bearer_keys", "cors_allow_origins", mode="before")
    @classmethod
    def _normalize_csv_values(cls, value: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:
        """Parse CSV-style env values into tuples."""

        return _parse_csv(value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()
