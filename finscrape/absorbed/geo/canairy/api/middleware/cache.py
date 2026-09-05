"""
Simple cache middleware
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class CacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # For now, just pass through
        # In production, implement proper caching logic
        response = await call_next(request)
        return response