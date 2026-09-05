"""
Simple rate limiting middleware
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next):
        client_id = request.client.host if request.client else "unknown"
        now = datetime.now()
        
        # Clean old entries
        self.clients[client_id] = [
            timestamp for timestamp in self.clients[client_id]
            if now - timestamp < timedelta(seconds=self.period)
        ]
        
        # Check rate limit
        if len(self.clients[client_id]) >= self.calls:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Add current request
        self.clients[client_id].append(now)
        
        # Process request
        response = await call_next(request)
        return response