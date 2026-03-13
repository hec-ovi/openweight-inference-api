"""Authentication tests."""

from __future__ import annotations

import asyncio

import pytest

from app.core.auth import require_bearer_token
from app.core.errors import AuthenticationError


def test_missing_bearer_token_returns_401(settings) -> None:
    """Requests without auth must be rejected."""

    with pytest.raises(AuthenticationError) as exc_info:
        asyncio.run(require_bearer_token(None, settings))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "invalid_api_key"
