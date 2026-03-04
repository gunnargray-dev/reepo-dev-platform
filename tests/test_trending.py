"""Tests for the Reepo trending module."""
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from src.db import init_db, insert_repo, _connect
from src.seed import seed_database
from src.trending import (
    init_trending_tables,
    record_star_snapshot,
    compute_trending,
    get_trending,
    get_new_repos,
)


def _make_repo(**overrides):
    base = {
        "github_id": 1,
        "owner": "test",
        "name": "test-repo",
        "full_name": "test/test-repo",
        "description": "A test repo",
        "stars": 100,
        "forks": 10,
        "language": "Python",
        "license": "MIT",
        "topics": ["ai"],
        "category_primary": "frameworks",
    }
    base.update(overrides)
    return base


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


# --- init_trending_tables ---

class TestInitTrendingTables:
    def test_creates_table(self, db_path):
        init_db(db_path)
        init_trending_tables(db_path)
        conn = _connect(db_path)
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='star_snapshots'"
        ).fetchone()
        conn.close()
        assert row is not None

    def test_idempotent(self, db_path):
        init_db(db_path)
        init_trending_tables(db_path)
        init_trending_tables(db_path)

    def test_creates_indexes(self, db_path):
        init_db(db_path)
        init_trending_tables(db_path)
        conn = _connect(db_path)
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_star%'"
        ).fetchall()
        conn.close()
        assert len(indexes) >= 2


# --- record_star_snapshot ---

class TestRecordStarSnapshot:
    def test_returns_count(self, seeded_db):
        count = record_star_snapshot(seeded_db)
        assert count == 50

    def test_inserts_rows(self, seeded_db):
        record_star_snapshot(seeded_db)
        conn = _connect(seeded_db)
        row = conn.execute("SELECT COUNT(*) as cnt FROM star_snapshots").fetchone()
        conn.close()
        assert row["cnt"] == 50

    def test_multiple_snapshots(self, seeded_db):
        record_star_snapshot(seeded_db)
        record_star_snapshot(seeded_db)
        conn = _connect(seeded_db)
        row = conn.execute("SELECT COUNT(*) as cnt FROM star_snapshots").fetchone()
        conn.close()
        assert row["cnt"] == 100

    def test_empty_db(self, db_path):
        init_db(db_path)
        count = record_star_snapshot(db_path)
        assert count == 0

    def test_snapshot_has_stars(self, seeded_db):
        record_star_snapshot(seeded_db)
        conn = _connect(seeded_db)
        row = conn.execute(
            "SELECT stars FROM star_snapshots ORDER BY stars DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert row["stars"] > 0

    def test_snapshot_has_timestamp(self, seeded_db):
        record_star_snapshot(seeded_db)
        conn = _connect(seeded_db)
        row = conn.execute("SELECT recorded_at FROM star_snapshots LIMIT 1").fetchone()
        conn.close()
        assert row["recorded_at"] is not None


# --- compute_trending ---

class TestComputeTrending:
    def test_empty_without_snapshots(self, seeded_db):
        init_trending_tables(seeded_db)
        result = compute_trending(seeded_db)
        assert result == []

    def test_returns_list(self, seeded_db):
        result = compute_trending(seeded_db)
        assert isinstance(result, list)

    def test_trending_with_delta(self, seeded_db):
        init_trending_tables(seeded_db)
        conn = _connect(seeded_db)
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=3)
        # Insert old snapshot with lower stars
        conn.execute(
            "INSERT INTO star_snapshots (repo_id, stars, recorded_at) VALUES (?, ?, ?)",
            (1, 50000, old.isoformat()),
        )
        # Insert recent snapshot with higher stars
        conn.execute(
            "INSERT INTO star_snapshots (repo_id, stars, recorded_at) VALUES (?, ?, ?)",
            (1, 95000, now.isoformat()),
        )
        conn.commit()
        conn.close()

        result = compute_trending(seeded_db, days=7)
        assert len(result) >= 1
        assert result[0]["star_delta"] > 0

    def test_trending_has_velocity(self, seeded_db):
        init_trending_tables(seeded_db)
        conn = _connect(seeded_db)
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=3)
        conn.execute(
            "INSERT INTO star_snapshots (repo_id, stars, recorded_at) VALUES (?, ?, ?)",
            (1, 80000, old.isoformat()),
        )
        conn.execute(
            "INSERT INTO star_snapshots (repo_id, stars, recorded_at) VALUES (?, ?, ?)",
            (1, 95000, now.isoformat()),
        )
        conn.commit()
        conn.close()

        result = compute_trending(seeded_db, days=7)
        assert result[0]["velocity"] > 0

    def test_trending_has_score(self, seeded_db):
        init_trending_tables(seeded_db)
        conn = _connect(seeded_db)
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=3)
        conn.execute(
            "INSERT INTO star_snapshots (repo_id, stars, recorded_at) VALUES (?, ?, ?)",
            (1, 50000, old.isoformat()),
        )
        conn.execute(
            "INSERT INTO star_snapshots (repo_id, stars, recorded_at) VALUES (?, ?, ?)",
            (1, 95000, now.isoformat()),
        )
        conn.commit()
        conn.close()

        result = compute_trending(seeded_db, days=7)
        assert "trending_score" in result[0]

    def test_no_delta_no_trending(self, seeded_db):
        record_star_snapshot(seeded_db)
        result = compute_trending(seeded_db, days=7)
        assert result == []


# --- get_trending ---

class TestGetTrending:
    def test_returns_list(self, seeded_db):
        result = get_trending(seeded_db)
        assert isinstance(result, list)

    def test_period_day(self, seeded_db):
        result = get_trending(seeded_db, period="day")
        assert isinstance(result, list)

    def test_period_week(self, seeded_db):
        result = get_trending(seeded_db, period="week")
        assert isinstance(result, list)

    def test_period_month(self, seeded_db):
        result = get_trending(seeded_db, period="month")
        assert isinstance(result, list)

    def test_limit(self, seeded_db):
        init_trending_tables(seeded_db)
        conn = _connect(seeded_db)
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=3)
        for repo_id in range(1, 11):
            conn.execute(
                "INSERT INTO star_snapshots (repo_id, stars, recorded_at) VALUES (?, ?, ?)",
                (repo_id, 100, old.isoformat()),
            )
            conn.execute(
                "INSERT INTO star_snapshots (repo_id, stars, recorded_at) VALUES (?, ?, ?)",
                (repo_id, 200 + repo_id * 10, now.isoformat()),
            )
        conn.commit()
        conn.close()

        result = get_trending(seeded_db, limit=5)
        assert len(result) <= 5

    def test_unknown_period_defaults(self, seeded_db):
        result = get_trending(seeded_db, period="invalid")
        assert isinstance(result, list)


# --- get_new_repos ---

class TestGetNewRepos:
    def test_returns_list(self, seeded_db):
        result = get_new_repos(seeded_db)
        assert isinstance(result, list)

    def test_respects_limit(self, seeded_db):
        result = get_new_repos(seeded_db, limit=5)
        assert len(result) <= 5

    def test_repos_have_data(self, seeded_db):
        result = get_new_repos(seeded_db, days=365)
        if result:
            assert "full_name" in result[0]
            assert "stars" in result[0]
