"""Export the generated OpenAPI schema to the static docs directory."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("API_BEARER_KEYS", "docs-token")
os.environ.setdefault("MODEL_PROFILE", "qwen3-light")
os.environ.setdefault("VLLM_BASE_URL", "http://vllm:8000")

from app.core.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


def main() -> None:
    """Write the OpenAPI document into `docs/openapi.json`."""

    get_settings.cache_clear()
    app = create_app()
    schema = app.openapi()

    output_path = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
