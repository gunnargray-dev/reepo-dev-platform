"""Tests for Built With module — submit, approve, reject, list, filter by repo."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.community.db import init_community_db
from src.community.built_with import (
    submit_project, get_project, list_projects,
    list_projects_for_repo, approve_project, reject_project,
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
        "github_id": 1, "owner": "org1", "name": "repo1",
        "full_name": "org1/repo1", "description": "First repo",
        "stars": 1000, "language": "Python", "category_primary": "frameworks",
    }, db_path)
    insert_repo({
        "github_id": 2, "owner": "org2", "name": "repo2",
        "full_name": "org2/repo2", "description": "Second repo",
        "stars": 500, "language": "Go", "category_primary": "apps",
    }, db_path)
    return db_path


class TestSubmitProject:
    def test_submit_returns_id(self, seeded_db):
        pid = submit_project(1, "My App", "A cool app", "https://myapp.com", [1], path=seeded_db)
        assert pid > 0

    def test_submit_creates_pending_project(self, seeded_db):
        pid = submit_project(1, "My App", "Cool", "https://x.com", [1], path=seeded_db)
        project = get_project(pid, path=seeded_db)
        assert project["status"] == "pending"
        assert project["title"] == "My App"

    def test_submit_links_repos(self, seeded_db):
        pid = submit_project(1, "App", "D", "https://x.com", [1, 2], path=seeded_db)
        project = get_project(pid, path=seeded_db)
        assert set(project["repo_ids"]) == {1, 2}

    def test_submit_with_screenshot(self, seeded_db):
        pid = submit_project(1, "App", "D", "https://x.com", [1],
                             screenshot_url="https://img.com/s.png", path=seeded_db)
        project = get_project(pid, path=seeded_db)
        assert project["screenshot_url"] == "https://img.com/s.png"


class TestGetProject:
    def test_get_existing(self, seeded_db):
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=seeded_db)
        project = get_project(pid, path=seeded_db)
        assert project is not None
        assert project["id"] == pid

    def test_get_nonexistent(self, seeded_db):
        assert get_project(999, path=seeded_db) is None


class TestListProjects:
    def test_list_approved_only(self, seeded_db):
        pid1 = submit_project(1, "App1", "D1", "https://x.com", [1], path=seeded_db)
        pid2 = submit_project(2, "App2", "D2", "https://y.com", [1], path=seeded_db)
        approve_project(pid1, path=seeded_db)
        projects = list_projects(status="approved", path=seeded_db)
        assert len(projects) == 1
        assert projects[0]["id"] == pid1

    def test_list_pending(self, seeded_db):
        submit_project(1, "App", "D", "https://x.com", [1], path=seeded_db)
        projects = list_projects(status="pending", path=seeded_db)
        assert len(projects) == 1

    def test_list_empty(self, seeded_db):
        projects = list_projects(status="approved", path=seeded_db)
        assert projects == []

    def test_sort_by_newest(self, seeded_db):
        pid1 = submit_project(1, "Old", "D", "https://x.com", [1], path=seeded_db)
        pid2 = submit_project(2, "New", "D", "https://y.com", [1], path=seeded_db)
        approve_project(pid1, path=seeded_db)
        approve_project(pid2, path=seeded_db)
        projects = list_projects(sort="newest", path=seeded_db)
        assert len(projects) == 2

    def test_list_with_limit_offset(self, seeded_db):
        for i in range(5):
            pid = submit_project(1, f"App{i}", "D", "https://x.com", [1], path=seeded_db)
            approve_project(pid, path=seeded_db)
        page1 = list_projects(limit=2, offset=0, path=seeded_db)
        page2 = list_projects(limit=2, offset=2, path=seeded_db)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]["id"] != page2[0]["id"]


class TestListProjectsForRepo:
    def test_filter_by_repo(self, seeded_db):
        pid1 = submit_project(1, "App1", "D", "https://x.com", [1], path=seeded_db)
        pid2 = submit_project(2, "App2", "D", "https://y.com", [2], path=seeded_db)
        approve_project(pid1, path=seeded_db)
        approve_project(pid2, path=seeded_db)
        results = list_projects_for_repo(1, path=seeded_db)
        assert len(results) == 1
        assert results[0]["id"] == pid1

    def test_only_approved_shown(self, seeded_db):
        submit_project(1, "Pending", "D", "https://x.com", [1], path=seeded_db)
        results = list_projects_for_repo(1, path=seeded_db)
        assert len(results) == 0


class TestApproveReject:
    def test_approve_pending(self, seeded_db):
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=seeded_db)
        assert approve_project(pid, path=seeded_db) is True
        project = get_project(pid, path=seeded_db)
        assert project["status"] == "approved"

    def test_approve_already_approved(self, seeded_db):
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=seeded_db)
        approve_project(pid, path=seeded_db)
        assert approve_project(pid, path=seeded_db) is False

    def test_reject_pending(self, seeded_db):
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=seeded_db)
        assert reject_project(pid, path=seeded_db) is True
        project = get_project(pid, path=seeded_db)
        assert project["status"] == "rejected"

    def test_reject_already_rejected(self, seeded_db):
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=seeded_db)
        reject_project(pid, path=seeded_db)
        assert reject_project(pid, path=seeded_db) is False

    def test_reject_nonexistent(self, seeded_db):
        assert reject_project(999, path=seeded_db) is False
