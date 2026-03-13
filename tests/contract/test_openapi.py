"""OpenAPI contract tests."""

from __future__ import annotations

from app.main import create_app


def test_openapi_contains_required_routes() -> None:
    """The generated schema must expose the required surface."""

    schema = create_app().openapi()
    assert schema["openapi"] == "3.1.0"
    required_paths = {
        "/v1/responses",
        "/v1/chat/completions",
        "/v1/models",
        "/health/live",
        "/health/ready",
        "/metrics",
    }
    assert required_paths.issubset(schema["paths"].keys())

