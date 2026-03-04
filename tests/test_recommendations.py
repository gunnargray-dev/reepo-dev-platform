"""Tests for recommendations — topic-based, collaborative, empty bookmarks, missing tables."""
import os
import tempfile

import pytest

from src.db import init_db, _connect, insert_repo
from src.growth.db import init_growth_db
from src.growth.recommendations import (
    get_recommendations_for_user,
    get_collaborative_recommendations,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_growth_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def db_with_bookmarks(db_path):
    """Create bookmarks table and seed data."""
    conn = _connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS bookmarks ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "repo_id INTEGER NOT NULL, "
        "created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    conn.close()

    # Insert repos in different categories
    for i in range(6):
        cat = "frameworks" if i < 3 else "apps"
        insert_repo({
            "github_id": i + 1, "owner": f"org{i}", "name": f"repo{i}",
            "full_name": f"org{i}/repo{i}", "stars": 1000 * (6 - i),
            "language": "Python", "category_primary": cat,
            "reepo_score": 80 - i * 10,
        }, db_path)

    # User 1 bookmarks frameworks repos
    conn = _connect(db_path)
    conn.execute("INSERT INTO bookmarks (user_id, repo_id) VALUES (1, 1)")
    conn.execute("INSERT INTO bookmarks (user_id, repo_id) VALUES (1, 2)")
    # User 2 bookmarks some same + different
    conn.execute("INSERT INTO bookmarks (user_id, repo_id) VALUES (2, 1)")
    conn.execute("INSERT INTO bookmarks (user_id, repo_id) VALUES (2, 4)")
    conn.execute("INSERT INTO bookmarks (user_id, repo_id) VALUES (2, 5)")
    conn.commit()
    conn.close()
    return db_path


class TestGetRecommendationsForUser:
    def test_no_bookmarks_table(self, db_path):
        """Gracefully returns [] when bookmarks table doesn't exist."""
        recs = get_recommendations_for_user(1, db_path)
        assert recs == []

    def test_with_bookmarks(self, db_with_bookmarks):
        recs = get_recommendations_for_user(1, db_with_bookmarks, limit=10)
        assert isinstance(recs, list)
        # Should recommend repos in same category but not already bookmarked
        rec_ids = [r["id"] for r in recs]
        assert 1 not in rec_ids  # already bookmarked
        assert 2 not in rec_ids  # already bookmarked

    def test_empty_bookmarks(self, db_with_bookmarks):
        """User 99 has no bookmarks — returns fallback top-scored repos."""
        recs = get_recommendations_for_user(99, db_with_bookmarks, limit=5)
        assert isinstance(recs, list)

    def test_limit_respected(self, db_with_bookmarks):
        recs = get_recommendations_for_user(1, db_with_bookmarks, limit=1)
        assert len(recs) <= 1


class TestGetCollaborativeRecommendations:
    def test_no_bookmarks_table(self, db_path):
        recs = get_collaborative_recommendations(1, db_path)
        assert recs == []

    def test_with_overlapping_users(self, db_with_bookmarks):
        """User 1 and 2 share repo 1; user 2 also has repos 4,5 — recommend those."""
        recs = get_collaborative_recommendations(1, db_with_bookmarks, limit=10)
        assert isinstance(recs, list)
        rec_ids = [r["id"] for r in recs]
        # Should not include repos user 1 already has
        assert 1 not in rec_ids
        assert 2 not in rec_ids

    def test_no_overlapping_users(self, db_with_bookmarks):
        """User 99 has no bookmarks, so no similar users."""
        recs = get_collaborative_recommendations(99, db_with_bookmarks, limit=10)
        assert recs == []

    def test_limit_respected(self, db_with_bookmarks):
        recs = get_collaborative_recommendations(1, db_with_bookmarks, limit=1)
        assert len(recs) <= 1
