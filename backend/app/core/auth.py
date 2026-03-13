"""Bearer token validation."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError

bearer_scheme = HTTPBearer(auto_error=False)


async def require_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    """Validate the incoming bearer token."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError()

    token = credentials.credentials
    if not settings.api_bearer_keys:
        raise AuthenticationError()

    if not any(secrets.compare_digest(token, allowed) for allowed in settings.api_bearer_keys):
        raise AuthenticationError()

    return token

