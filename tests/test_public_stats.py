"""Tests for the Reepo public stats API endpoint."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.db import init_db, insert_repo
from src.search import init_fts
from src.trending import init_trending_tables
from src.monetization.db import init_monetization_db
from src.analytics import init_analytics_db
from src.community.contributors import init_contributor_db
from src.server import create_app


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_fts(path)
    init_trending_tables(path)
    init_monetization_db(path)
    init_analytics_db(path)
    init_contributor_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def seeded_db(db_path):
    for i in range(10):
        insert_repo({
            "github_id": 90000 + i,
            "owner": "stats-org",
            "name": f"stats-repo-{i}",
            "full_name": f"stats-org/stats-repo-{i}",
            "description": f"Stats test repo {i}",
            "url": f"https://github.com/stats-org/stats-repo-{i}",
            "stars": 2000 - i * 100,
            "forks": 100 + i,
            "language": ["Python", "TypeScript", "Rust", "Go", "Java",
                         "Python", "TypeScript", "Rust", "Go", "Java"][i],
            "license": "MIT",
            "category_primary": ["frameworks", "tools", "models", "datasets", "libraries",
                                 "frameworks", "tools", "models", "datasets", "libraries"][i],
            "reepo_score": 95 - i * 5,
        }, db_path)
    return db_path


@pytest.fixture
def client(seeded_db):
    app = create_app(db_path=seeded_db)
    return TestClient(app)


@pytest.fixture
def empty_client(db_path):
    app = create_app(db_path=db_path)
    return TestClient(app)


class TestPublicStatsEndpoint:
    def test_returns_200(self, client):
        resp = client.get("/api/public-stats")
        assert resp.status_code == 200

    def test_response_structure(self, client):
        data = client.get("/api/public-stats").json()
        assert "total_repos" in data
        assert "repos_by_category" in data
        assert "repos_by_language" in data
        assert "avg_reepo_score" in data
        assert "median_score" in data
        assert "score_distribution" in data
        assert "index_growth" in data
        assert "top_repos_by_score" in data
        assert "newest_repos" in data

    def test_total_repos_count(self, client):
        data = client.get("/api/public-stats").json()
        assert data["total_repos"] == 10

    def test_repos_by_category(self, client):
        data = client.get("/api/public-stats").json()
        cats = data["repos_by_category"]
        assert isinstance(cats, dict)
        assert len(cats) > 0

    def test_repos_by_language(self, client):
        data = client.get("/api/public-stats").json()
        langs = data["repos_by_language"]
        assert isinstance(langs, dict)
        assert "Python" in langs

    def test_avg_score_present(self, client):
        data = client.get("/api/public-stats").json()
        assert data["avg_reepo_score"] is not None
        assert isinstance(data["avg_reepo_score"], (int, float))

    def test_median_score(self, client):
        data = client.get("/api/public-stats").json()
        assert isinstance(data["median_score"], (int, float))
        assert data["median_score"] > 0

    def test_score_distribution(self, client):
        data = client.get("/api/public-stats").json()
        dist = data["score_distribution"]
        assert "excellent_80_plus" in dist
        assert "good_60_79" in dist
        assert "fair_40_59" in dist
        assert "poor_below_40" in dist

    def test_top_repos_by_score(self, client):
        data = client.get("/api/public-stats").json()
        top = data["top_repos_by_score"]
        assert isinstance(top, list)
        assert len(top) > 0
        # First should be highest score
        assert top[0]["reepo_score"] >= top[-1]["reepo_score"]

    def test_top_repos_have_fields(self, client):
        data = client.get("/api/public-stats").json()
        top = data["top_repos_by_score"]
        for repo in top:
            assert "full_name" in repo
            assert "reepo_score" in repo
            assert "stars" in repo

    def test_newest_repos(self, client):
        data = client.get("/api/public-stats").json()
        newest = data["newest_repos"]
        assert isinstance(newest, list)
        assert len(newest) > 0

    def test_newest_repos_have_fields(self, client):
        data = client.get("/api/public-stats").json()
        newest = data["newest_repos"]
        for repo in newest:
            assert "full_name" in repo
            assert "description" in repo

    def test_index_growth(self, client):
        data = client.get("/api/public-stats").json()
        growth = data["index_growth"]
        assert isinstance(growth, list)

    def test_empty_db(self, empty_client):
        data = empty_client.get("/api/public-stats").json()
        assert data["total_repos"] == 0
        assert data["top_repos_by_score"] == []
        assert data["newest_repos"] == []

    def test_top_repos_limited(self, client):
        data = client.get("/api/public-stats").json()
        assert len(data["top_repos_by_score"]) <= 10

    def test_newest_repos_limited(self, client):
        data = client.get("/api/public-stats").json()
        assert len(data["newest_repos"]) <= 10


class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
