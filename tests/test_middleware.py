"""Tests for the Reepo middleware — rate limiting and caching."""
import time

import pytest

from src.middleware import RateLimiter, SimpleCache, search_cache, detail_cache


# --- SimpleCache ---

class TestSimpleCache:
    def test_set_and_get(self):
        cache = SimpleCache()
        cache.set("key", "value", ttl=60)
        assert cache.get("key") == "value"

    def test_get_miss(self):
        cache = SimpleCache()
        assert cache.get("missing") is None

    def test_ttl_expiry(self):
        cache = SimpleCache()
        cache.set("key", "value", ttl=0)
        time.sleep(0.01)
        assert cache.get("key") is None

    def test_overwrite(self):
        cache = SimpleCache()
        cache.set("key", "old", ttl=60)
        cache.set("key", "new", ttl=60)
        assert cache.get("key") == "new"

    def test_clear(self):
        cache = SimpleCache()
        cache.set("k1", "v1", ttl=60)
        cache.set("k2", "v2", ttl=60)
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_multiple_keys(self):
        cache = SimpleCache()
        cache.set("k1", "v1", ttl=60)
        cache.set("k2", "v2", ttl=60)
        assert cache.get("k1") == "v1"
        assert cache.get("k2") == "v2"

    def test_stores_complex_objects(self):
        cache = SimpleCache()
        data = {"results": [1, 2, 3], "total": 3}
        cache.set("key", data, ttl=60)
        assert cache.get("key") == data

    def test_stores_none_value(self):
        cache = SimpleCache()
        cache.set("key", None, ttl=60)
        # get returns None for both miss and stored None - that's OK
        # just verify it doesn't crash
        cache.get("key")

    def test_stores_list(self):
        cache = SimpleCache()
        cache.set("key", [1, 2, 3], ttl=60)
        assert cache.get("key") == [1, 2, 3]

    def test_stores_int(self):
        cache = SimpleCache()
        cache.set("key", 42, ttl=60)
        assert cache.get("key") == 42


# --- SimpleCache.make_key ---

class TestSimpleCacheMakeKey:
    def test_deterministic(self):
        cache = SimpleCache()
        k1 = cache.make_key("search", q="test", page=1)
        k2 = cache.make_key("search", q="test", page=1)
        assert k1 == k2

    def test_different_params(self):
        cache = SimpleCache()
        k1 = cache.make_key("search", q="test")
        k2 = cache.make_key("search", q="other")
        assert k1 != k2

    def test_different_prefix(self):
        cache = SimpleCache()
        k1 = cache.make_key("search", q="test")
        k2 = cache.make_key("detail", q="test")
        assert k1 != k2

    def test_ignores_none_params(self):
        cache = SimpleCache()
        k1 = cache.make_key("search", q="test", category=None)
        k2 = cache.make_key("search", q="test")
        assert k1 == k2

    def test_order_independent(self):
        cache = SimpleCache()
        k1 = cache.make_key("search", q="test", page=1)
        k2 = cache.make_key("search", page=1, q="test")
        assert k1 == k2

    def test_returns_string(self):
        cache = SimpleCache()
        key = cache.make_key("test")
        assert isinstance(key, str)
        assert len(key) > 0


# --- Global cache instances ---

class TestGlobalCaches:
    def test_search_cache_exists(self):
        assert search_cache is not None
        assert isinstance(search_cache, SimpleCache)

    def test_detail_cache_exists(self):
        assert detail_cache is not None
        assert isinstance(detail_cache, SimpleCache)

    def test_caches_independent(self):
        search_cache.clear()
        detail_cache.clear()
        search_cache.set("k", "search", ttl=60)
        assert detail_cache.get("k") is None


# --- RateLimiter (integration via FastAPI test) ---

class TestRateLimiterIntegration:
    def test_rate_limiter_allows_requests(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(RateLimiter, max_requests=10, window_seconds=60)

        @app.get("/test")
        def test_endpoint():
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200

    def test_rate_limiter_blocks_excess(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(RateLimiter, max_requests=3, window_seconds=60)

        @app.get("/test")
        def test_endpoint():
            return {"ok": True}

        client = TestClient(app)
        for _ in range(3):
            resp = client.get("/test")
            assert resp.status_code == 200

        resp = client.get("/test")
        assert resp.status_code == 429

    def test_rate_limit_response_body(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(RateLimiter, max_requests=1, window_seconds=60)

        @app.get("/test")
        def test_endpoint():
            return {"ok": True}

        client = TestClient(app)
        client.get("/test")
        resp = client.get("/test")
        assert resp.status_code == 429
        assert "Rate limit" in resp.json()["detail"]

    def test_rate_limit_retry_after(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(RateLimiter, max_requests=1, window_seconds=30)

        @app.get("/test")
        def test_endpoint():
            return {"ok": True}

        client = TestClient(app)
        client.get("/test")
        resp = client.get("/test")
        assert resp.headers.get("Retry-After") == "30"
