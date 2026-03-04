"""Tests for community, admin, and blog API endpoints."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.db import init_db, insert_repo
from src.community.db import init_community_db
from src.community.built_with import submit_project, approve_project
from src.community.comments import add_comment, flag_comment
from src.community.submissions import submit_repo
from src.community.blog import create_post, publish_post
from src.server import create_app


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app = create_app(path)
    with TestClient(app) as c:
        yield c, path
    os.unlink(path)


@pytest.fixture
def seeded_client(client):
    c, path = client
    insert_repo({
        "github_id": 1, "owner": "org1", "name": "repo1",
        "full_name": "org1/repo1", "description": "A test repo",
        "stars": 1000, "language": "Python", "category_primary": "frameworks",
    }, path)
    insert_repo({
        "github_id": 2, "owner": "org2", "name": "repo2",
        "full_name": "org2/repo2", "description": "Another repo",
        "stars": 500, "language": "Go", "category_primary": "apps",
    }, path)
    return c, path


# --- Built With API ---

class TestBuiltWithAPI:
    def test_submit_project(self, seeded_client):
        c, path = seeded_client
        resp = c.post("/api/built-with", json={
            "user_id": 1, "title": "My App", "description": "Cool app",
            "url": "https://myapp.com", "repo_ids": [1],
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    def test_list_projects_empty(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/built-with")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_approved_projects(self, seeded_client):
        c, path = seeded_client
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=path)
        approve_project(pid, path=path)
        resp = c.get("/api/built-with")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_project(self, seeded_client):
        c, path = seeded_client
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=path)
        resp = c.get(f"/api/built-with/{pid}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "App"

    def test_get_project_not_found(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/built-with/999")
        assert resp.status_code == 404

    def test_toggle_upvote(self, seeded_client):
        c, path = seeded_client
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=path)
        resp = c.post(f"/api/built-with/{pid}/upvote?user_id=10")
        assert resp.status_code == 200
        assert resp.json()["upvoted"] is True
        resp = c.post(f"/api/built-with/{pid}/upvote?user_id=10")
        assert resp.json()["upvoted"] is False

    def test_repo_built_with(self, seeded_client):
        c, path = seeded_client
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=path)
        approve_project(pid, path=path)
        resp = c.get("/api/repos/org1/repo1/built-with")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_repo_built_with_not_found(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/repos/nonexistent/repo/built-with")
        assert resp.status_code == 404


# --- Comments API ---

class TestCommentsAPI:
    def test_add_comment(self, seeded_client):
        c, _ = seeded_client
        resp = c.post("/api/repos/org1/repo1/comments", json={
            "user_id": 1, "body": "Great repo!",
        })
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_get_comments(self, seeded_client):
        c, path = seeded_client
        from src.db import get_repo
        repo = get_repo("org1", "repo1", path=path)
        add_comment(1, repo["id"], "First comment", path=path)
        resp = c.get("/api/repos/org1/repo1/comments")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_comments_repo_not_found(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/repos/nonexistent/repo/comments")
        assert resp.status_code == 404

    def test_add_comment_repo_not_found(self, seeded_client):
        c, _ = seeded_client
        resp = c.post("/api/repos/nonexistent/repo/comments", json={
            "user_id": 1, "body": "Comment",
        })
        assert resp.status_code == 404


# --- Submissions API ---

class TestSubmissionsAPI:
    def test_submit_repo(self, seeded_client):
        c, _ = seeded_client
        resp = c.post("/api/submissions", json={
            "user_id": 1, "github_url": "https://github.com/new/repo",
        })
        assert resp.status_code == 200

    def test_submit_invalid_url(self, seeded_client):
        c, _ = seeded_client
        resp = c.post("/api/submissions", json={
            "user_id": 1, "github_url": "not-a-url",
        })
        assert resp.status_code == 400


# --- Digest API ---

class TestDigestAPI:
    def test_get_latest_digest_none(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/digest/latest")
        assert resp.status_code == 404

    def test_get_latest_digest_after_save(self, seeded_client):
        c, path = seeded_client
        from src.community.digest import generate_digest, save_digest
        digest = generate_digest(path=path)
        save_digest(digest, path=path)
        resp = c.get("/api/digest/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert "content" in data
        assert "issue_number" in data


# --- Admin API ---

class TestAdminAPI:
    def test_get_stats(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/admin/stats")
        assert resp.status_code == 200
        assert "total_repos" in resp.json()

    def test_get_moderation(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/api/admin/moderation")
        assert resp.status_code == 200
        data = resp.json()
        assert "pending_built_with" in data
        assert "flagged_comments" in data
        assert "pending_submissions" in data

    def test_approve_built_with(self, seeded_client):
        c, path = seeded_client
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=path)
        resp = c.post(f"/api/admin/built-with/{pid}/approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_reject_built_with(self, seeded_client):
        c, path = seeded_client
        pid = submit_project(1, "App", "D", "https://x.com", [1], path=path)
        resp = c.post(f"/api/admin/built-with/{pid}/reject")
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_approve_built_with_not_found(self, seeded_client):
        c, _ = seeded_client
        resp = c.post("/api/admin/built-with/999/approve")
        assert resp.status_code == 404

    def test_approve_submission(self, seeded_client):
        c, path = seeded_client
        result = submit_repo(1, "https://github.com/new/repo", path=path)
        resp = c.post(f"/api/admin/submissions/{result['submission_id']}/approve")
        assert resp.status_code == 200

    def test_reject_submission(self, seeded_client):
        c, path = seeded_client
        result = submit_repo(1, "https://github.com/new/repo", path=path)
        resp = c.post(f"/api/admin/submissions/{result['submission_id']}/reject")
        assert resp.status_code == 200

    def test_remove_comment(self, seeded_client):
        c, path = seeded_client
        from src.db import get_repo
        repo = get_repo("org1", "repo1", path=path)
        cid = add_comment(1, repo["id"], "Bad comment", path=path)
        resp = c.post(f"/api/admin/comments/{cid}/remove")
        assert resp.status_code == 200

    def test_remove_comment_not_found(self, seeded_client):
        c, _ = seeded_client
        resp = c.post("/api/admin/comments/999/remove")
        assert resp.status_code == 404


# --- Blog API ---

class TestBlogAPI:
    def test_create_post(self, client):
        c, path = client
        resp = c.post("/api/blog", json={
            "slug": "hello", "title": "Hello", "body": "World",
            "author": "admin", "tags": ["test"],
        })
        assert resp.status_code == 200
        assert resp.json()["slug"] == "hello"

    def test_list_posts_empty(self, client):
        c, _ = client
        resp = c.get("/api/blog")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_published_posts(self, client):
        c, path = client
        create_post("test", "Test", "Body", "admin", path=path)
        publish_post("test", path=path)
        resp = c.get("/api/blog")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_post(self, client):
        c, path = client
        create_post("slug", "Title", "Body", "admin", path=path)
        resp = c.get("/api/blog/slug")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Title"

    def test_get_post_not_found(self, client):
        c, _ = client
        resp = c.get("/api/blog/nonexistent")
        assert resp.status_code == 404

    def test_rss_feed(self, client):
        c, path = client
        create_post("rss", "RSS Post", "Body", "admin", path=path)
        publish_post("rss", path=path)
        resp = c.get("/api/blog/rss")
        assert resp.status_code == 200
        assert "application/rss+xml" in resp.headers["content-type"]
        assert "<rss" in resp.text

    def test_rss_feed_empty(self, client):
        c, _ = client
        resp = c.get("/api/blog/rss")
        assert resp.status_code == 200
        assert "<item>" not in resp.text
