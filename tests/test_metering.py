"""Tests for the Reepo API metering — usage tracking, limits, stats."""
import os
import tempfile

import pytest

from src.db import init_db
from src.monetization.db import init_monetization_db
from src.monetization.gates import FREE_API_LIMIT, PRO_API_LIMIT
from src.monetization.metering import (
    track_api_usage,
    get_requests_today,
    check_api_limit,
    get_usage_stats,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_monetization_db(path)
    yield path
    os.unlink(path)


class TestTrackApiUsage:
    def test_track_single_request(self, db_path):
        track_api_usage("key-1", "/api/search", db_path)
        assert get_requests_today("key-1", db_path) == 1

    def test_track_multiple_requests(self, db_path):
        for i in range(10):
            track_api_usage("key-2", f"/api/endpoint-{i}", db_path)
        assert get_requests_today("key-2", db_path) == 10

    def test_track_different_keys(self, db_path):
        track_api_usage("key-a", "/api/search", db_path)
        track_api_usage("key-b", "/api/search", db_path)
        assert get_requests_today("key-a", db_path) == 1
        assert get_requests_today("key-b", db_path) == 1

    def test_track_same_endpoint(self, db_path):
        for _ in range(3):
            track_api_usage("key-3", "/api/repos", db_path)
        assert get_requests_today("key-3", db_path) == 3


class TestGetRequestsToday:
    def test_no_requests(self, db_path):
        assert get_requests_today("new-key", db_path) == 0

    def test_counts_correctly(self, db_path):
        for _ in range(7):
            track_api_usage("count-key", "/api/test", db_path)
        assert get_requests_today("count-key", db_path) == 7


class TestCheckApiLimit:
    def test_under_limit_free(self, db_path):
        assert check_api_limit("free-key", is_pro=False, path=db_path) is True

    def test_under_limit_pro(self, db_path):
        assert check_api_limit("pro-key", is_pro=True, path=db_path) is True

    def test_at_free_limit(self, db_path):
        for _ in range(FREE_API_LIMIT):
            track_api_usage("limit-key", "/api/test", db_path)
        assert check_api_limit("limit-key", is_pro=False, path=db_path) is False

    def test_over_free_under_pro(self, db_path):
        for _ in range(FREE_API_LIMIT + 1):
            track_api_usage("mixed-key", "/api/test", db_path)
        assert check_api_limit("mixed-key", is_pro=False, path=db_path) is False
        assert check_api_limit("mixed-key", is_pro=True, path=db_path) is True


class TestGetUsageStats:
    def test_stats_structure(self, db_path):
        stats = get_usage_stats("stats-key", path=db_path)
        assert "requests_today" in stats
        assert "limit" in stats
        assert "remaining" in stats
        assert "reset_at" in stats
        assert "is_pro" in stats

    def test_stats_free_user(self, db_path):
        stats = get_usage_stats("free-stats", is_pro=False, path=db_path)
        assert stats["limit"] == FREE_API_LIMIT
        assert stats["remaining"] == FREE_API_LIMIT
        assert stats["requests_today"] == 0
        assert stats["is_pro"] is False

    def test_stats_pro_user(self, db_path):
        stats = get_usage_stats("pro-stats", is_pro=True, path=db_path)
        assert stats["limit"] == PRO_API_LIMIT
        assert stats["remaining"] == PRO_API_LIMIT
        assert stats["is_pro"] is True

    def test_stats_after_usage(self, db_path):
        for _ in range(25):
            track_api_usage("used-key", "/api/test", db_path)
        stats = get_usage_stats("used-key", is_pro=False, path=db_path)
        assert stats["requests_today"] == 25
        assert stats["remaining"] == FREE_API_LIMIT - 25

    def test_stats_remaining_never_negative(self, db_path):
        for _ in range(FREE_API_LIMIT + 50):
            track_api_usage("over-key", "/api/test", db_path)
        stats = get_usage_stats("over-key", is_pro=False, path=db_path)
        assert stats["remaining"] == 0

    def test_stats_reset_at_is_future(self, db_path):
        from datetime import datetime, timezone
        stats = get_usage_stats("time-key", path=db_path)
        reset = datetime.fromisoformat(stats["reset_at"])
        assert reset > datetime.now(timezone.utc)
