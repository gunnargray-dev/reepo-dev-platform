"""Reepo middleware — rate limiting and caching for the API."""
from __future__ import annotations

import hashlib
import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimiter(BaseHTTPMiddleware):
    """In-memory rate limiter: configurable requests per window per IP."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        cutoff = now - self.window_seconds

        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > cutoff
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._requests[client_ip].append(now)
        response = await call_next(request)
        return response


class SimpleCache:
    """Simple TTL cache for API responses."""

    def __init__(self):
        self._cache: dict[str, tuple[float, any]] = {}

    def get(self, key: str) -> any | None:
        if key in self._cache:
            expires, value = self._cache[key]
            if time.time() < expires:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: any, ttl: int = 300) -> None:
        self._cache[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        self._cache.clear()

    def make_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and keyword arguments."""
        parts = sorted(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        raw = f"{prefix}:{':'.join(parts)}"
        return hashlib.md5(raw.encode()).hexdigest()


# Global cache instances
search_cache = SimpleCache()  # 5-min TTL for search
detail_cache = SimpleCache()  # 15-min TTL for repo detail
