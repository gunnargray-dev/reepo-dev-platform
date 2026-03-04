"""Tests for admin module — stats and moderation queue."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.community.db import init_community_db
from src.community.built_with import submit_project
from src.community.comments import add_comment, flag_comment
from src.community.submissions import submit_repo
from src.community.admin import get_admin_stats, get_moderation_queue


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_community_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def seeded_db(db_path):
    for i in range(3):
        insert_repo({
            "github_id": i + 1, "owner": f"org{i}", "name": f"repo{i}",
            "full_name": f"org{i}/repo{i}", "stars": 100,
            "language": "Python", "category_primary": "frameworks",
        }, db_path)
    return db_path


class TestGetAdminStats:
    def test_empty_db(self, db_path):
        stats = get_admin_stats(path=db_path)
        assert stats["total_repos"] == 0
        assert stats["pending_submissions"] == 0
        assert stats["flagged_comments"] == 0
        assert stats["pending_built_with"] == 0
        assert stats["total_comments"] == 0
        assert stats["total_built_with"] == 0

    def test_with_data(self, seeded_db):
        submit_project(1, "App", "D", "https://x.com", [1], path=seeded_db)
        add_comment(1, 1, "Comment", path=seeded_db)
        cid = add_comment(2, 1, "Bad", path=seeded_db)
        flag_comment(cid, path=seeded_db)
        submit_repo(1, "https://github.com/new/repo", path=seeded_db)

        stats = get_admin_stats(path=seeded_db)
        assert stats["total_repos"] == 3
        assert stats["pending_submissions"] == 1
        assert stats["flagged_comments"] == 1
        assert stats["pending_built_with"] == 1
        assert stats["total_comments"] == 2
        assert stats["total_built_with"] == 1


class TestGetModerationQueue:
    def test_empty_queue(self, db_path):
        queue = get_moderation_queue(path=db_path)
        assert queue["pending_built_with"] == []
        assert queue["flagged_comments"] == []
        assert queue["pending_submissions"] == []

    def test_with_items(self, seeded_db):
        submit_project(1, "App", "D", "https://x.com", [1], path=seeded_db)
        cid = add_comment(1, 1, "Bad", path=seeded_db)
        flag_comment(cid, path=seeded_db)
        submit_repo(1, "https://github.com/new/repo", path=seeded_db)

        queue = get_moderation_queue(path=seeded_db)
        assert len(queue["pending_built_with"]) == 1
        assert len(queue["flagged_comments"]) == 1
        assert len(queue["pending_submissions"]) == 1

    def test_approved_not_in_queue(self, seeded_db):
        from src.community.built_with import approve_project
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=seeded_db)
        approve_project(pid, path=seeded_db)
        queue = get_moderation_queue(path=seeded_db)
        assert len(queue["pending_built_with"]) == 0
