"""Tests for the Reepo LRU cache — TTL, eviction, invalidation, thread safety."""
import time
import threading

import pytest

from src.cache import LRUCache


@pytest.fixture
def cache():
    return LRUCache(max_size=5, default_ttl=10)


class TestLRUCacheGet:
    def test_get_missing_key(self, cache):
        assert cache.get("nonexistent") is None

    def test_get_existing_key(self, cache):
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_get_expired_key(self):
        c = LRUCache(max_size=5, default_ttl=0)
        c.set("key", "value", ttl=0)
        time.sleep(0.01)
        assert c.get("key") is None

    def test_get_updates_lru_order(self, cache):
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.get("a")  # Move 'a' to end
        cache.set("d", 4)
        cache.set("e", 5)
        cache.set("f", 6)  # Should evict 'b' (least recently used)
        assert cache.get("a") == 1
        assert cache.get("b") is None


class TestLRUCacheSet:
    def test_set_new_key(self, cache):
        cache.set("key", "value")
        assert cache.size == 1

    def test_set_overwrites_existing(self, cache):
        cache.set("key", "v1")
        cache.set("key", "v2")
        assert cache.get("key") == "v2"
        assert cache.size == 1

    def test_set_with_custom_ttl(self):
        c = LRUCache(max_size=5, default_ttl=100)
        c.set("key", "value", ttl=0)
        time.sleep(0.01)
        assert c.get("key") is None

    def test_evicts_oldest_when_full(self, cache):
        for i in range(6):
            cache.set(f"key-{i}", i)
        assert cache.size == 5
        assert cache.get("key-0") is None
        assert cache.get("key-5") == 5

    def test_stores_various_types(self, cache):
        cache.set("str", "hello")
        cache.set("int", 42)
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"a": 1})
        assert cache.get("str") == "hello"
        assert cache.get("int") == 42
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"a": 1}


class TestLRUCacheInvalidate:
    def test_invalidate_existing(self, cache):
        cache.set("key", "value")
        assert cache.invalidate("key") is True
        assert cache.get("key") is None

    def test_invalidate_missing(self, cache):
        assert cache.invalidate("nope") is False

    def test_invalidate_decreases_size(self, cache):
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.size == 2
        cache.invalidate("a")
        assert cache.size == 1


class TestLRUCacheInvalidatePrefix:
    def test_invalidate_matching_prefix(self, cache):
        cache.set("user:1", "alice")
        cache.set("user:2", "bob")
        cache.set("repo:1", "torch")
        removed = cache.invalidate_prefix("user:")
        assert removed == 2
        assert cache.get("user:1") is None
        assert cache.get("repo:1") == "torch"

    def test_invalidate_no_match(self, cache):
        cache.set("key", "value")
        assert cache.invalidate_prefix("nope:") == 0

    def test_invalidate_all_with_empty_prefix(self, cache):
        cache.set("a", 1)
        cache.set("b", 2)
        removed = cache.invalidate_prefix("")
        assert removed == 2
        assert cache.size == 0


class TestLRUCacheClear:
    def test_clear_empties_cache(self, cache):
        for i in range(3):
            cache.set(f"key-{i}", i)
        cache.clear()
        assert cache.size == 0


class TestLRUCacheStats:
    def test_initial_stats(self, cache):
        stats = cache.stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["max_size"] == 5

    def test_stats_after_hits_and_misses(self, cache):
        cache.set("key", "value")
        cache.get("key")  # hit
        cache.get("key")  # hit
        cache.get("miss")  # miss
        stats = cache.stats
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(66.7, abs=0.1)

    def test_stats_size_tracks(self, cache):
        cache.set("a", 1)
        assert cache.stats["size"] == 1
        cache.set("b", 2)
        assert cache.stats["size"] == 2


class TestLRUCacheMakeKey:
    def test_deterministic(self):
        k1 = LRUCache.make_key("prefix", a="1", b="2")
        k2 = LRUCache.make_key("prefix", a="1", b="2")
        assert k1 == k2

    def test_order_independent(self):
        k1 = LRUCache.make_key("p", b="2", a="1")
        k2 = LRUCache.make_key("p", a="1", b="2")
        assert k1 == k2

    def test_different_prefix(self):
        k1 = LRUCache.make_key("x", a="1")
        k2 = LRUCache.make_key("y", a="1")
        assert k1 != k2

    def test_none_values_excluded(self):
        k1 = LRUCache.make_key("p", a="1", b=None)
        k2 = LRUCache.make_key("p", a="1")
        assert k1 == k2


class TestLRUCacheThreadSafety:
    def test_concurrent_writes(self):
        c = LRUCache(max_size=100, default_ttl=60)
        errors = []

        def writer(prefix):
            try:
                for i in range(50):
                    c.set(f"{prefix}-{i}", i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(f"t{t}",)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert c.size <= 100

    def test_concurrent_reads_and_writes(self):
        c = LRUCache(max_size=50, default_ttl=60)
        for i in range(20):
            c.set(f"key-{i}", i)

        errors = []

        def reader():
            try:
                for i in range(20):
                    c.get(f"key-{i}")
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for i in range(20, 40):
                    c.set(f"key-{i}", i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(3)]
        threads.append(threading.Thread(target=writer))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
