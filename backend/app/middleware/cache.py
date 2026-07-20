"""Caching middleware for vertical scaling."""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class CacheMiddleware(BaseHTTPMiddleware):
    """Simple in-memory cache for GET requests."""

    def __init__(self, app, ttl_seconds: int = 300):
        super().__init__(app)
        self.ttl_seconds = ttl_seconds
        self.cache = {}

    async def dispatch(self, request: Request, call_next):
        if request.method != "GET":
            return await call_next(request)

        cache_key = f"{request.url.path}:{request.url.query}"
        if cache_key in self.cache:
            cached_response, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.ttl_seconds:
                return JSONResponse(content=cached_response)

        response = await call_next(request)
        if response.status_code == 200:
            import json
            if hasattr(response, 'body_iterator'):
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                data = json.loads(body)
            else:
                data = response.content if hasattr(response, 'content') else {}
            self.cache[cache_key] = (data, time.time())
            return JSONResponse(content=data)

        return response
