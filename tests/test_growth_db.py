"""Tests for growth database initialization."""
import os
import sqlite3
import tempfile

import pytest

from src.db import init_db
from src.growth.db import init_growth_db


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_growth_db(path)
    yield path
    os.unlink(path)


class TestInitGrowthDb:
    def test_creates_repo_events_table(self, db_path):
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='repo_events'"
        ).fetchone()
        conn.close()
        assert tables is not None

    def test_repo_events_columns(self, db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("PRAGMA table_info(repo_events)")
        columns = {row["name"] for row in cur.fetchall()}
        conn.close()
        assert "id" in columns
        assert "repo_id" in columns
        assert "event_type" in columns
        assert "title" in columns
        assert "description" in columns
        assert "data" in columns
        assert "occurred_at" in columns
        assert "created_at" in columns

    def test_idempotent(self, db_path):
        init_growth_db(db_path)
        init_growth_db(db_path)
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table' AND name='repo_events'"
        ).fetchone()
        conn.close()
        assert tables[0] == 1

    def test_indexes_created(self, db_path):
        conn = sqlite3.connect(db_path)
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_repo_events%'"
        ).fetchall()
        conn.close()
        index_names = {row[0] for row in indexes}
        assert "idx_repo_events_repo" in index_names
        assert "idx_repo_events_type" in index_names
        assert "idx_repo_events_occurred" in index_names
