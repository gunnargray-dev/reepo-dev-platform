"""Tests for the Reepo export API (Pro only) — JSON and CSV export."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.db import init_db, insert_repo
from src.search import init_fts
from src.monetization.db import init_monetization_db
from src.monetization.stripe_billing import create_checkout_session
from src.server import create_app


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_monetization_db(path)
    yield path
    os.unlink(path)


def _make_repo(**overrides):
    defaults = {
        "github_id": 4000,
        "owner": "export-org",
        "name": "export-repo",
        "full_name": "export-org/export-repo",
        "description": "A repo for export tests",
        "stars": 200,
        "forks": 20,
        "language": "Python",
        "topics": '["ml", "ai"]',
        "category_primary": "frameworks",
        "reepo_score": 70,
        "license": "MIT",
    }
    defaults.update(overrides)
    return defaults


def _make_pro_user(user_id, path):
    create_checkout_session(user_id, "pro_monthly", "https://ok", "https://cancel", path=path)


@pytest.fixture
def seeded_db(db_path):
    for i in range(10):
        insert_repo(
            _make_repo(
                github_id=4000 + i,
                name=f"export-repo-{i}",
                full_name=f"export-org/export-repo-{i}",
                description=f"Export test repo {i}",
                stars=100 + i * 50,
            ),
            db_path,
        )
    init_fts(db_path)
    return db_path


@pytest.fixture
def client(seeded_db):
    app = create_app(db_path=seeded_db)
    return TestClient(app)


class TestExportSearch:
    def test_requires_pro(self, client):
        resp = client.get("/api/export/search?q=export&user_id=1")
        assert resp.status_code == 403

    def test_requires_auth(self, client):
        resp = client.get("/api/export/search?q=export")
        assert resp.status_code == 401

    def test_export_json(self, client, seeded_db):
        _make_pro_user(1, seeded_db)
        resp = client.get("/api/export/search?q=export&format=json&user_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert "repos" in data
        assert "total" in data

    def test_export_csv(self, client, seeded_db):
        _make_pro_user(1, seeded_db)
        resp = client.get("/api/export/search?q=export&format=csv&user_id=1")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        content = resp.text
        assert "full_name" in content  # CSV header

    def test_export_csv_has_rows(self, client, seeded_db):
        _make_pro_user(1, seeded_db)
        resp = client.get("/api/export/search?q=export&format=csv&user_id=1")
        lines = resp.text.strip().split("\n")
        assert len(lines) >= 2  # Header + at least one row

    def test_export_empty_search(self, client, seeded_db):
        _make_pro_user(1, seeded_db)
        resp = client.get("/api/export/search?q=nonexistentxyz&format=json&user_id=1")
        assert resp.status_code == 200


class TestExportRepo:
    def test_requires_pro(self, client):
        resp = client.get("/api/export/repo/export-org/export-repo-0?user_id=1")
        assert resp.status_code == 403

    def test_export_repo_json(self, client, seeded_db):
        _make_pro_user(1, seeded_db)
        resp = client.get("/api/export/repo/export-org/export-repo-0?user_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert "repo" in data
        assert "similar_repos" in data
        assert "score_history" in data

    def test_repo_not_found(self, client, seeded_db):
        _make_pro_user(1, seeded_db)
        resp = client.get("/api/export/repo/no-one/no-repo?user_id=1")
        assert resp.status_code == 404

    def test_export_repo_has_details(self, client, seeded_db):
        _make_pro_user(1, seeded_db)
        resp = client.get("/api/export/repo/export-org/export-repo-0?user_id=1")
        repo = resp.json()["repo"]
        assert repo["full_name"] == "export-org/export-repo-0"
        assert "stars" in repo
