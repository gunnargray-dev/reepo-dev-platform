"""Tests for the Reepo analytics pipeline — page views, search queries, summaries."""
import os
import tempfile

import pytest

from src.db import init_db
from src.analytics import (
    init_analytics_db,
    hash_ip,
    record_page_view,
    record_search_query,
    get_analytics_summary,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_analytics_db(path)
    yield path
    os.unlink(path)


class TestHashIp:
    def test_deterministic(self):
        assert hash_ip("127.0.0.1") == hash_ip("127.0.0.1")

    def test_different_ips(self):
        assert hash_ip("127.0.0.1") != hash_ip("192.168.1.1")

    def test_length(self):
        assert len(hash_ip("10.0.0.1")) == 16

    def test_empty_string(self):
        result = hash_ip("")
        assert isinstance(result, str)
        assert len(result) == 16


class TestRecordPageView:
    def test_record_single_view(self, db_path):
        record_page_view("/", db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        assert summary["total_views"] == 1

    def test_record_with_all_fields(self, db_path):
        record_page_view(
            "/api/repos",
            referrer="https://google.com",
            user_agent="Mozilla/5.0",
            ip="127.0.0.1",
            user_id=42,
            db_path=db_path,
        )
        summary = get_analytics_summary(db_path, days=1)
        assert summary["total_views"] == 1
        assert summary["unique_visitors"] == 1

    def test_record_multiple_views(self, db_path):
        for i in range(15):
            record_page_view(f"/page-{i}", db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        assert summary["total_views"] == 15

    def test_different_ips_counted_as_unique(self, db_path):
        for i in range(5):
            record_page_view("/", ip=f"10.0.0.{i}", db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        assert summary["unique_visitors"] == 5

    def test_same_ip_counted_once(self, db_path):
        for _ in range(3):
            record_page_view("/", ip="192.168.1.1", db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        assert summary["unique_visitors"] == 1

    def test_no_ip_not_counted_as_visitor(self, db_path):
        record_page_view("/", ip="", db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        assert summary["unique_visitors"] == 0


class TestRecordSearchQuery:
    def test_record_single_query(self, db_path):
        record_search_query("pytorch", db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        assert summary["conversion_funnel"]["searches"] == 1

    def test_record_with_all_fields(self, db_path):
        record_search_query(
            "langchain",
            filters='{"language": "Python"}',
            results_count=42,
            user_id=1,
            db_path=db_path,
        )
        summary = get_analytics_summary(db_path, days=1)
        assert summary["conversion_funnel"]["searches"] == 1

    def test_record_multiple_queries(self, db_path):
        for q in ["torch", "keras", "jax", "tensorflow", "onnx"]:
            record_search_query(q, db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        assert summary["conversion_funnel"]["searches"] == 5

    def test_top_search_queries(self, db_path):
        for _ in range(5):
            record_search_query("popular-query", results_count=10, db_path=db_path)
        record_search_query("rare-query", results_count=2, db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        top = summary["top_search_queries"]
        assert len(top) >= 1
        assert top[0]["query"] == "popular-query"
        assert top[0]["count"] == 5


class TestGetAnalyticsSummary:
    def test_empty_db(self, db_path):
        summary = get_analytics_summary(db_path, days=30)
        assert summary["total_views"] == 0
        assert summary["unique_visitors"] == 0
        assert summary["top_pages"] == []
        assert summary["top_search_queries"] == []

    def test_summary_structure(self, db_path):
        summary = get_analytics_summary(db_path, days=30)
        assert "total_views" in summary
        assert "unique_visitors" in summary
        assert "top_pages" in summary
        assert "top_search_queries" in summary
        assert "top_repos_viewed" in summary
        assert "conversion_funnel" in summary
        assert "period_days" in summary

    def test_period_days_returned(self, db_path):
        for days in [7, 30, 90]:
            summary = get_analytics_summary(db_path, days=days)
            assert summary["period_days"] == days

    def test_top_pages_ordering(self, db_path):
        for _ in range(10):
            record_page_view("/popular", db_path=db_path)
        for _ in range(3):
            record_page_view("/less-popular", db_path=db_path)
        record_page_view("/rare", db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        pages = summary["top_pages"]
        assert len(pages) == 3
        assert pages[0]["path"] == "/popular"
        assert pages[0]["views"] == 10
        assert pages[1]["path"] == "/less-popular"

    def test_conversion_funnel_structure(self, db_path):
        summary = get_analytics_summary(db_path, days=1)
        funnel = summary["conversion_funnel"]
        assert "visits" in funnel
        assert "searches" in funnel
        assert "views" in funnel
        assert "saves" in funnel
        assert "signups" in funnel
        assert "pro_upgrades" in funnel

    def test_repo_views_tracked(self, db_path):
        record_page_view("/api/repos/org/repo-1", db_path=db_path)
        record_page_view("/api/repos/org/repo-1", db_path=db_path)
        record_page_view("/api/repos/org/repo-2", db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        assert summary["conversion_funnel"]["views"] == 3
        assert len(summary["top_repos_viewed"]) == 2

    def test_conversion_funnel_views_match(self, db_path):
        for _ in range(5):
            record_page_view("/home", db_path=db_path)
        for _ in range(3):
            record_page_view("/api/repos/a/b", db_path=db_path)
        summary = get_analytics_summary(db_path, days=1)
        assert summary["conversion_funnel"]["visits"] == 8
        assert summary["conversion_funnel"]["views"] == 3
