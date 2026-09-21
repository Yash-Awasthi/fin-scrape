"""API-key auth for the mutating routes (X-API-Key or Bearer)."""

from __future__ import annotations

import hmac

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
    # Constant-time compare: a plain `!=` leaks the matching prefix length through
    # response timing. Encoded first so a non-ASCII key cannot raise out of compare.
    expected = get_settings().api_key
    if not supplied or not hmac.compare_digest(
        supplied.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")
