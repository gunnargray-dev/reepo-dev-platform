"""Tests for upvotes module — toggle, count, idempotency."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.community.db import init_community_db
from src.community.built_with import submit_project, approve_project
from src.community.upvotes import toggle_upvote, get_upvote_count, has_upvoted


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_community_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def project_db(db_path):
    insert_repo({
        "github_id": 1, "owner": "org1", "name": "repo1",
        "full_name": "org1/repo1", "stars": 100, "language": "Python",
        "category_primary": "frameworks",
    }, db_path)
    pid = submit_project(1, "App", "Desc", "https://x.com", [1], path=db_path)
    approve_project(pid, path=db_path)
    return db_path, pid


class TestToggleUpvote:
    def test_upvote_returns_true(self, project_db):
        path, pid = project_db
        assert toggle_upvote(10, pid, path=path) is True

    def test_remove_upvote_returns_false(self, project_db):
        path, pid = project_db
        toggle_upvote(10, pid, path=path)
        assert toggle_upvote(10, pid, path=path) is False

    def test_re_upvote_after_remove(self, project_db):
        path, pid = project_db
        toggle_upvote(10, pid, path=path)
        toggle_upvote(10, pid, path=path)
        assert toggle_upvote(10, pid, path=path) is True

    def test_multiple_users_upvote(self, project_db):
        path, pid = project_db
        toggle_upvote(10, pid, path=path)
        toggle_upvote(20, pid, path=path)
        toggle_upvote(30, pid, path=path)
        assert get_upvote_count(pid, path=path) == 3


class TestGetUpvoteCount:
    def test_initial_count_zero(self, project_db):
        path, pid = project_db
        assert get_upvote_count(pid, path=path) == 0

    def test_count_after_upvote(self, project_db):
        path, pid = project_db
        toggle_upvote(10, pid, path=path)
        assert get_upvote_count(pid, path=path) == 1

    def test_count_after_remove(self, project_db):
        path, pid = project_db
        toggle_upvote(10, pid, path=path)
        toggle_upvote(10, pid, path=path)
        assert get_upvote_count(pid, path=path) == 0

    def test_count_nonexistent_project(self, db_path):
        assert get_upvote_count(999, path=db_path) == 0

    def test_count_never_goes_negative(self, project_db):
        """Ensure upvote_count doesn't go below 0 if toggled on empty."""
        path, pid = project_db
        # Count is already 0, ensure we don't go negative
        assert get_upvote_count(pid, path=path) == 0


class TestHasUpvoted:
    def test_not_upvoted(self, project_db):
        path, pid = project_db
        assert has_upvoted(10, pid, path=path) is False

    def test_has_upvoted(self, project_db):
        path, pid = project_db
        toggle_upvote(10, pid, path=path)
        assert has_upvoted(10, pid, path=path) is True

    def test_after_remove(self, project_db):
        path, pid = project_db
        toggle_upvote(10, pid, path=path)
        toggle_upvote(10, pid, path=path)
        assert has_upvoted(10, pid, path=path) is False

    def test_different_users(self, project_db):
        path, pid = project_db
        toggle_upvote(10, pid, path=path)
        assert has_upvoted(10, pid, path=path) is True
        assert has_upvoted(20, pid, path=path) is False
