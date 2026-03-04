"""Tests for the Reepo comparison tool API (Pro only)."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.db import init_db, insert_repo
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
        "github_id": 3000,
        "owner": "test",
        "name": "repo",
        "full_name": "test/repo",
        "description": "Test repo",
        "stars": 100,
        "forks": 10,
        "language": "Python",
        "topics": '["ai"]',
        "category_primary": "frameworks",
        "reepo_score": 75,
        "score_breakdown": '{"maintenance": 80}',
        "license": "MIT",
        "open_issues": 5,
    }
    defaults.update(overrides)
    return defaults


def _make_pro_user(user_id, path):
    create_checkout_session(user_id, "pro_monthly", "https://ok", "https://cancel", path=path)


@pytest.fixture
def seeded_db(db_path):
    ids = []
    for i in range(5):
        rid = insert_repo(
            _make_repo(
                github_id=3000 + i,
                name=f"repo-{i}",
                full_name=f"test/repo-{i}",
                stars=100 * (i + 1),
                reepo_score=60 + i * 5,
            ),
            db_path,
        )
        ids.append(rid)
    return db_path, ids


@pytest.fixture
def client(seeded_db):
    db_path, _ = seeded_db
    app = create_app(db_path=db_path)
    return TestClient(app)


class TestCompareEndpoint:
    def test_requires_pro(self, client):
        resp = client.post("/api/compare?repo_ids=1,2&user_id=1")
        assert resp.status_code == 403

    def test_requires_auth(self, client):
        resp = client.post("/api/compare?repo_ids=1,2")
        assert resp.status_code == 401

    def test_compare_two_repos(self, client, seeded_db):
        db_path, ids = seeded_db
        _make_pro_user(1, db_path)
        resp = client.post(f"/api/compare?repo_ids={ids[0]},{ids[1]}&user_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert len(data["repos"]) == 2

    def test_compare_five_repos(self, client, seeded_db):
        db_path, ids = seeded_db
        _make_pro_user(1, db_path)
        id_str = ",".join(str(i) for i in ids[:5])
        resp = client.post(f"/api/compare?repo_ids={id_str}&user_id=1")
        assert resp.status_code == 200
        assert resp.json()["count"] == 5

    def test_too_few_repos(self, client, seeded_db):
        db_path, ids = seeded_db
        _make_pro_user(1, db_path)
        resp = client.post(f"/api/compare?repo_ids={ids[0]}&user_id=1")
        assert resp.status_code == 400

    def test_too_many_repos(self, client, seeded_db):
        db_path, ids = seeded_db
        _make_pro_user(1, db_path)
        resp = client.post("/api/compare?repo_ids=1,2,3,4,5,6&user_id=1")
        assert resp.status_code in (400, 404)

    def test_repo_not_found(self, client, seeded_db):
        db_path, ids = seeded_db
        _make_pro_user(1, db_path)
        resp = client.post(f"/api/compare?repo_ids={ids[0]},99999&user_id=1")
        assert resp.status_code == 404

    def test_comparison_data_fields(self, client, seeded_db):
        db_path, ids = seeded_db
        _make_pro_user(1, db_path)
        resp = client.post(f"/api/compare?repo_ids={ids[0]},{ids[1]}&user_id=1")
        assert resp.status_code == 200
        repo = resp.json()["repos"][0]
        assert "full_name" in repo
        assert "stars" in repo
        assert "forks" in repo
        assert "reepo_score" in repo
        assert "language" in repo
        assert "license" in repo

    def test_compare_returns_correct_repos(self, client, seeded_db):
        db_path, ids = seeded_db
        _make_pro_user(1, db_path)
        resp = client.post(f"/api/compare?repo_ids={ids[0]},{ids[2]}&user_id=1")
        data = resp.json()
        names = [r["full_name"] for r in data["repos"]]
        assert "test/repo-0" in names
        assert "test/repo-2" in names
