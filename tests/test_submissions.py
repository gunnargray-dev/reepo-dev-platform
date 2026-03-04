"""Tests for submissions module — submit, validate, approve, reject, duplicate detection."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.community.db import init_community_db
from src.community.submissions import (
    submit_repo, list_pending_submissions,
    approve_submission, reject_submission,
)


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
        "github_id": 1, "owner": "existing", "name": "repo",
        "full_name": "existing/repo", "stars": 100, "language": "Python",
        "category_primary": "frameworks",
    }, db_path)
    return db_path


class TestSubmitRepo:
    def test_valid_submission(self, db_path):
        result = submit_repo(1, "https://github.com/org/new-repo", path=db_path)
        assert result["ok"] is True
        assert "submission_id" in result

    def test_invalid_url(self, db_path):
        result = submit_repo(1, "not-a-url", path=db_path)
        assert result["ok"] is False
        assert "error" in result

    def test_invalid_url_no_github(self, db_path):
        result = submit_repo(1, "https://gitlab.com/org/repo", path=db_path)
        assert result["ok"] is False

    def test_duplicate_submission(self, db_path):
        submit_repo(1, "https://github.com/org/new-repo", path=db_path)
        result = submit_repo(2, "https://github.com/org/new-repo", path=db_path)
        assert result["ok"] is False
        assert "Already submitted" in result["error"]

    def test_already_indexed(self, seeded_db):
        result = submit_repo(1, "https://github.com/existing/repo", path=seeded_db)
        assert result["ok"] is False
        assert "already indexed" in result["error"]

    def test_url_trailing_slash_normalized(self, db_path):
        result = submit_repo(1, "https://github.com/org/repo/", path=db_path)
        assert result["ok"] is True

    def test_url_whitespace_stripped(self, db_path):
        result = submit_repo(1, "  https://github.com/org/repo  ", path=db_path)
        assert result["ok"] is True


class TestListPendingSubmissions:
    def test_list_pending(self, db_path):
        submit_repo(1, "https://github.com/org/repo1", path=db_path)
        submit_repo(2, "https://github.com/org/repo2", path=db_path)
        pending = list_pending_submissions(path=db_path)
        assert len(pending) == 2

    def test_list_empty(self, db_path):
        assert list_pending_submissions(path=db_path) == []

    def test_approved_not_in_pending(self, db_path):
        result = submit_repo(1, "https://github.com/org/repo1", path=db_path)
        approve_submission(result["submission_id"], path=db_path)
        pending = list_pending_submissions(path=db_path)
        assert len(pending) == 0


class TestApproveRejectSubmission:
    def test_approve(self, db_path):
        result = submit_repo(1, "https://github.com/org/repo1", path=db_path)
        assert approve_submission(result["submission_id"], path=db_path) is True

    def test_approve_already_approved(self, db_path):
        result = submit_repo(1, "https://github.com/org/repo1", path=db_path)
        approve_submission(result["submission_id"], path=db_path)
        assert approve_submission(result["submission_id"], path=db_path) is False

    def test_reject(self, db_path):
        result = submit_repo(1, "https://github.com/org/repo1", path=db_path)
        assert reject_submission(result["submission_id"], path=db_path) is True

    def test_reject_already_rejected(self, db_path):
        result = submit_repo(1, "https://github.com/org/repo1", path=db_path)
        reject_submission(result["submission_id"], path=db_path)
        assert reject_submission(result["submission_id"], path=db_path) is False

    def test_reject_nonexistent(self, db_path):
        assert reject_submission(999, path=db_path) is False

    def test_approve_nonexistent(self, db_path):
        assert approve_submission(999, path=db_path) is False
