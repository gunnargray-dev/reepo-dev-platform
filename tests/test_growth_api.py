"""Tests for growth API endpoints — badges, scheduler, recommendations, changelog."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.db import init_db, insert_repo, _connect
from src.growth.db import init_growth_db
from src.growth.changelog import record_event
from src.server import create_app


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app = create_app(path)
    with TestClient(app) as c:
        yield c, path
    os.unlink(path)


@pytest.fixture
def seeded_client(client):
    c, path = client
    insert_repo({
        "github_id": 1, "owner": "org1", "name": "repo1",
        "full_name": "org1/repo1", "description": "A test repo",
        "stars": 1000, "language": "Python", "category_primary": "frameworks",
        "reepo_score": 85,
    }, path)
    insert_repo({
        "github_id": 2, "owner": "org2", "name": "repo2",
        "full_name": "org2/repo2", "description": "Another repo",
        "stars": 200, "language": "Go", "category_primary": "apps",
        "reepo_score": 30,
    }, path)
    return c, path


# --- Badge API ---

class TestBadgeAPI:
    def test_get_badge_svg(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/badge/org1/repo1.svg")
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.headers["content-type"]
        assert "<svg" in resp.text
        assert "85" in resp.text

    def test_badge_cache_control(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/badge/org1/repo1.svg")
        assert "max-age=3600" in resp.headers.get("cache-control", "")

    def test_badge_flat_square_style(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/badge/org1/repo1.svg?style=flat-square")
        assert resp.status_code == 200
        assert "<svg" in resp.text

    def test_badge_for_the_badge_style(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/badge/org1/repo1.svg?style=for-the-badge")
        assert resp.status_code == 200
        assert 'height="28"' in resp.text

    def test_badge_not_found(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/badge/nonexistent/repo.svg")
        assert resp.status_code == 404


# --- Scheduler API ---

class TestSchedulerAPI:
    def test_run_crawl(self, seeded_client):
        c, _ = seeded_client
        resp = c.post("/api/admin/crawl/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "ran_at" in data

    def test_crawl_status(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/admin/crawl/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "last_run" in data


# --- Recommendations API ---

class TestRecommendationsAPI:
    def test_recommendations_no_bookmarks_table(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/recommendations?user_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data

    def test_recommendations_with_method(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/recommendations?user_id=1&method=collaborative")
        assert resp.status_code == 200
        assert resp.json()["method"] == "collaborative"

    def test_recommendations_with_limit(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/recommendations?user_id=1&limit=5")
        assert resp.status_code == 200

    def test_recommendations_with_bookmarks(self, seeded_client):
        c, path = seeded_client
        conn = _connect(path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS bookmarks ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  user_id INTEGER NOT NULL,"
            "  repo_id INTEGER NOT NULL,"
            "  UNIQUE(user_id, repo_id))"
        )
        conn.execute("INSERT INTO bookmarks (user_id, repo_id) VALUES (1, 1)")
        conn.commit()
        conn.close()
        resp = c.get("/api/recommendations?user_id=1")
        assert resp.status_code == 200


# --- Changelog API ---

class TestChangelogAPI:
    def test_get_changelog(self, seeded_client):
        c, path = seeded_client
        record_event(1, "test", "Test Event", path=path)
        resp = c.get("/api/repos/org1/repo1/changelog")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["events"][0]["title"] == "Test Event"

    def test_changelog_empty(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/repos/org1/repo1/changelog")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_changelog_repo_not_found(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/repos/nonexistent/repo/changelog")
        assert resp.status_code == 404

    def test_changelog_with_limit(self, seeded_client):
        c, path = seeded_client
        for i in range(5):
            record_event(1, "test", f"Event {i}", path=path)
        resp = c.get("/api/repos/org1/repo1/changelog?limit=2")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2
