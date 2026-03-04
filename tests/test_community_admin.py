"""Tests for admin module — stats, moderation queue, comment removal."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.community.db import init_community_db
from src.community.built_with import submit_project
from src.community.comments import add_comment, flag_comment
from src.community.submissions import submit_repo
from src.community.admin import get_admin_stats, get_moderation_queue, remove_comment


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
    insert_repo({
        "github_id": 1, "owner": "org1", "name": "repo1",
        "full_name": "org1/repo1", "stars": 100, "language": "Python",
        "category_primary": "frameworks",
    }, db_path)
    return db_path


class TestGetAdminStats:
    def test_empty_stats(self, db_path):
        stats = get_admin_stats(path=db_path)
        assert stats["total_repos"] == 0
        assert stats["total_comments"] == 0
        assert stats["total_built_with"] == 0
        assert stats["pending_submissions"] == 0
        assert stats["flagged_comments"] == 0
        assert stats["pending_built_with"] == 0

    def test_stats_with_repos(self, seeded_db):
        stats = get_admin_stats(path=seeded_db)
        assert stats["total_repos"] == 1

    def test_stats_with_comments(self, seeded_db):
        add_comment(1, 1, "Comment 1", path=seeded_db)
        add_comment(2, 1, "Comment 2", path=seeded_db)
        stats = get_admin_stats(path=seeded_db)
        assert stats["total_comments"] == 2

    def test_stats_with_flagged_comments(self, seeded_db):
        cid = add_comment(1, 1, "Bad comment", path=seeded_db)
        flag_comment(cid, path=seeded_db)
        stats = get_admin_stats(path=seeded_db)
        assert stats["flagged_comments"] == 1

    def test_stats_with_built_with(self, seeded_db):
        submit_project(1, "App", "Desc", "https://x.com", [1], path=seeded_db)
        stats = get_admin_stats(path=seeded_db)
        assert stats["total_built_with"] == 1
        assert stats["pending_built_with"] == 1

    def test_stats_with_pending_submissions(self, seeded_db):
        submit_repo(1, "https://github.com/org/new-repo", path=seeded_db)
        stats = get_admin_stats(path=seeded_db)
        assert stats["pending_submissions"] == 1


class TestGetModerationQueue:
    def test_empty_queue(self, db_path):
        queue = get_moderation_queue(path=db_path)
        assert queue["pending_built_with"] == []
        assert queue["flagged_comments"] == []
        assert queue["pending_submissions"] == []

    def test_pending_built_with_in_queue(self, seeded_db):
        submit_project(1, "App", "Desc", "https://x.com", [1], path=seeded_db)
        queue = get_moderation_queue(path=seeded_db)
        assert len(queue["pending_built_with"]) == 1
        assert queue["pending_built_with"][0]["title"] == "App"

    def test_flagged_comments_in_queue(self, seeded_db):
        cid = add_comment(1, 1, "Bad comment", path=seeded_db)
        flag_comment(cid, path=seeded_db)
        queue = get_moderation_queue(path=seeded_db)
        assert len(queue["flagged_comments"]) == 1
        assert queue["flagged_comments"][0]["body"] == "Bad comment"

    def test_pending_submissions_in_queue(self, seeded_db):
        submit_repo(1, "https://github.com/org/new-repo", path=seeded_db)
        queue = get_moderation_queue(path=seeded_db)
        assert len(queue["pending_submissions"]) == 1

    def test_multiple_items_in_queue(self, seeded_db):
        submit_project(1, "App1", "D", "https://x.com", [1], path=seeded_db)
        submit_project(2, "App2", "D", "https://y.com", [1], path=seeded_db)
        cid = add_comment(1, 1, "Bad", path=seeded_db)
        flag_comment(cid, path=seeded_db)
        submit_repo(1, "https://github.com/org/new-repo", path=seeded_db)
        queue = get_moderation_queue(path=seeded_db)
        assert len(queue["pending_built_with"]) == 2
        assert len(queue["flagged_comments"]) == 1
        assert len(queue["pending_submissions"]) == 1


class TestRemoveComment:
    def test_remove_existing(self, seeded_db):
        cid = add_comment(1, 1, "Delete me", path=seeded_db)
        assert remove_comment(cid, path=seeded_db) is True

    def test_remove_nonexistent(self, db_path):
        assert remove_comment(999, path=db_path) is False

    def test_remove_reduces_count(self, seeded_db):
        cid1 = add_comment(1, 1, "First", path=seeded_db)
        add_comment(2, 1, "Second", path=seeded_db)
        remove_comment(cid1, path=seeded_db)
        stats = get_admin_stats(path=seeded_db)
        assert stats["total_comments"] == 1
