"""API-key auth for the mutating routes (X-API-Key or Bearer)."""

from __future__ import annotations

from fastapi import Header, HTTPException

from server.settings import get_settings


async def require_api_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    """Accept `X-API-Key: <key>` or `Authorization: Bearer <key>`. 401 otherwise."""
    supplied = x_api_key
    if not supplied and authorization and authorization.lower().startswith("bearer "):
        supplied = authorization[7:].strip()
    if not supplied or supplied != get_settings().api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
