"""Tests for the Reepo FastAPI API endpoints."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.seed import seed_database
from src.server import create_app
from src.trending import init_trending_tables, record_star_snapshot
from src.db import _connect

from datetime import datetime, timedelta, timezone


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def seeded_db(db_path):
    seed_database(db_path)
    return db_path


@pytest.fixture
def client(seeded_db):
    app = create_app(db_path=seeded_db)
    return TestClient(app)


@pytest.fixture
def empty_client(db_path):
    from src.db import init_db
    init_db(db_path)
    app = create_app(db_path=db_path)
    return TestClient(app)


# --- Health ---

class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# --- Search API ---

class TestSearchAPI:
    def test_search_no_query(self, client):
        resp = client.get("/api/search")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "total" in data
        assert data["total"] == 50

    def test_search_with_query(self, client):
        resp = client.get("/api/search?q=langchain")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_search_with_category(self, client):
        resp = client.get("/api/search?category=agents")
        assert resp.status_code == 200
        data = resp.json()
        for r in data["results"]:
            assert r["category_primary"] == "agents"

    def test_search_with_language(self, client):
        resp = client.get("/api/search?language=Python")
        assert resp.status_code == 200
        data = resp.json()
        for r in data["results"]:
            assert r["language"] == "Python"

    def test_search_with_min_score(self, client):
        resp = client.get("/api/search?min_score=60")
        assert resp.status_code == 200
        data = resp.json()
        for r in data["results"]:
            assert r["reepo_score"] >= 60

    def test_search_sort_stars(self, client):
        resp = client.get("/api/search?sort=stars&per_page=50")
        data = resp.json()
        stars = [r["stars"] for r in data["results"]]
        assert stars == sorted(stars, reverse=True)

    def test_search_pagination(self, client):
        resp = client.get("/api/search?per_page=5&page=1")
        data = resp.json()
        assert len(data["results"]) == 5
        assert data["page"] == 1
        assert data["pages"] >= 2

    def test_search_page_2(self, client):
        r1 = client.get("/api/search?per_page=5&page=1").json()
        r2 = client.get("/api/search?per_page=5&page=2").json()
        ids1 = {r["id"] for r in r1["results"]}
        ids2 = {r["id"] for r in r2["results"]}
        assert ids1.isdisjoint(ids2)

    def test_search_no_results(self, client):
        resp = client.get("/api/search?q=xyznonexistent999")
        data = resp.json()
        assert data["total"] == 0

    def test_search_empty_db(self, empty_client):
        resp = empty_client.get("/api/search?q=test")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# --- Repo Detail API ---

class TestRepoAPI:
    def test_get_repo(self, client):
        resp = client.get("/api/repos/langchain-ai/langchain")
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "langchain-ai/langchain"
        assert data["stars"] == 95000

    def test_repo_has_score(self, client):
        resp = client.get("/api/repos/langchain-ai/langchain")
        data = resp.json()
        assert data["reepo_score"] is not None

    def test_repo_has_topics(self, client):
        resp = client.get("/api/repos/langchain-ai/langchain")
        data = resp.json()
        assert isinstance(data["topics"], list)
        assert len(data["topics"]) > 0

    def test_repo_not_found(self, client):
        resp = client.get("/api/repos/nonexistent/repo")
        assert resp.status_code == 404

    def test_repo_score_breakdown(self, client):
        resp = client.get("/api/repos/langchain-ai/langchain")
        data = resp.json()
        assert data["score_breakdown"] is not None
        assert "maintenance_health" in data["score_breakdown"]


# --- Similar Repos API ---

class TestSimilarAPI:
    def test_similar(self, client):
        resp = client.get("/api/repos/langchain-ai/langchain/similar")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "total" in data

    def test_similar_not_empty(self, client):
        resp = client.get("/api/repos/langchain-ai/langchain/similar")
        data = resp.json()
        assert data["total"] > 0

    def test_similar_excludes_self(self, client):
        resp = client.get("/api/repos/langchain-ai/langchain/similar")
        data = resp.json()
        for r in data["results"]:
            assert r["full_name"] != "langchain-ai/langchain"

    def test_similar_limit(self, client):
        resp = client.get("/api/repos/langchain-ai/langchain/similar?limit=3")
        data = resp.json()
        assert len(data["results"]) <= 3

    def test_similar_nonexistent(self, client):
        resp = client.get("/api/repos/nonexistent/repo/similar")
        data = resp.json()
        assert data["total"] == 0


# --- Categories API ---

class TestCategoriesAPI:
    def test_categories(self, client):
        resp = client.get("/api/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert len(data["categories"]) == 10

    def test_categories_have_count(self, client):
        resp = client.get("/api/categories")
        data = resp.json()
        for cat in data["categories"]:
            assert "repo_count" in cat

    def test_categories_have_name(self, client):
        resp = client.get("/api/categories")
        data = resp.json()
        for cat in data["categories"]:
            assert "name" in cat
            assert "slug" in cat

    def test_categories_total(self, client):
        resp = client.get("/api/categories")
        data = resp.json()
        total = sum(c["repo_count"] for c in data["categories"])
        assert total > 0


# --- Trending API ---

class TestTrendingAPI:
    def test_trending(self, client):
        resp = client.get("/api/trending")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "period" in data

    def test_trending_period(self, client):
        resp = client.get("/api/trending?period=month")
        data = resp.json()
        assert data["period"] == "month"

    def test_trending_limit(self, client):
        resp = client.get("/api/trending?limit=5")
        data = resp.json()
        assert len(data["results"]) <= 5

    def test_new_repos(self, client):
        resp = client.get("/api/trending/new")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data


# --- Stats API ---

class TestStatsAPI:
    def test_stats(self, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_repos"] == 50

    def test_stats_by_category(self, client):
        resp = client.get("/api/stats")
        data = resp.json()
        assert "by_category" in data
        assert len(data["by_category"]) > 0

    def test_stats_by_language(self, client):
        resp = client.get("/api/stats")
        data = resp.json()
        assert "by_language" in data
        assert "Python" in data["by_language"]

    def test_stats_score_stats(self, client):
        resp = client.get("/api/stats")
        data = resp.json()
        assert "score_stats" in data
        assert data["score_stats"]["avg_score"] > 0

    def test_stats_empty_db(self, empty_client):
        resp = empty_client.get("/api/stats")
        data = resp.json()
        assert data["total_repos"] == 0
