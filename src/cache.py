"""Reepo enhanced caching — LRU with TTL, warming, invalidation."""
from __future__ import annotations

import hashlib
import time
import threading
from collections import OrderedDict


class LRUCache:
    """Thread-safe LRU cache with per-entry TTL."""

    def __init__(self, max_size: int = 1024, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[float, any]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> any | None:
        """Get a value. Returns None if missing or expired."""
        with self._lock:
            if key in self._cache:
                expires, value = self._cache[key]
                if time.time() < expires:
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return value
                del self._cache[key]
            self._misses += 1
            return None

    def set(self, key: str, value: any, ttl: int | None = None) -> None:
        """Set a value with optional TTL override."""
        ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (time.time() + ttl, value)

    def invalidate(self, key: str) -> bool:
        """Remove a specific key. Returns True if it existed."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Remove all keys starting with prefix. Returns count removed."""
        with self._lock:
            to_remove = [k for k in self._cache if k.startswith(prefix)]
            for k in to_remove:
                del self._cache[k]
            return len(to_remove)

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 1) if total > 0 else 0.0,
            "size": self.size,
            "max_size": self.max_size,
        }

    @staticmethod
    def make_key(prefix: str, **kwargs) -> str:
        """Generate deterministic cache key from prefix and kwargs."""
        parts = sorted(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        raw = f"{prefix}:{':'.join(parts)}"
        return hashlib.md5(raw.encode()).hexdigest()


def warm_cache(cache: LRUCache, db_path: str) -> int:
    """Pre-populate cache with commonly accessed data. Returns count of entries warmed."""
    from src.db import list_repos, get_categories, count_repos, get_score_stats
    from src.trending import get_trending

    count = 0

    # Top repos by stars
    key = LRUCache.make_key("list_repos", sort_by="stars", limit="50")
    cache.set(key, list_repos(path=db_path, sort_by="stars", limit=50), ttl=600)
    count += 1

    # Top repos by score
    key = LRUCache.make_key("list_repos", sort_by="reepo_score", limit="50")
    cache.set(key, list_repos(path=db_path, sort_by="reepo_score", limit=50), ttl=600)
    count += 1

    # Categories
    key = LRUCache.make_key("categories")
    cache.set(key, get_categories(db_path), ttl=3600)
    count += 1

    # Stats
    key = LRUCache.make_key("stats")
    cache.set(key, {"total": count_repos(db_path), "score_stats": get_score_stats(db_path)}, ttl=600)
    count += 1

    # Trending
    for period in ("day", "week", "month"):
        key = LRUCache.make_key("trending", period=period)
        try:
            cache.set(key, get_trending(db_path, period=period, limit=20), ttl=600)
            count += 1
        except Exception:
            pass

    return count


# Global cache instances
query_cache = LRUCache(max_size=2048, default_ttl=300)
repo_cache = LRUCache(max_size=512, default_ttl=900)
