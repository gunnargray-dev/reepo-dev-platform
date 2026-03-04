"""Tests for Phase 5 — Community and Built With Showcase."""
import json
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.community.db import init_community_db
from src.community.built_with import (
    submit_project, get_project, list_projects, list_projects_for_repo,
    approve_project, reject_project,
)
from src.community.upvotes import toggle_upvote, get_upvote_count, has_upvoted
from src.community.comments import (
    add_comment, get_comments, update_comment, delete_comment,
    flag_comment, get_flagged_comments,
)
from src.community.digest import (
    generate_digest, render_digest_html, render_digest_markdown,
    save_digest, get_latest_digest,
)
from src.community.submissions import (
    submit_repo, list_pending_submissions, approve_submission, reject_submission,
)
from src.community.admin import get_admin_stats, get_moderation_queue, remove_comment
from src.community.blog import (
    create_post, get_post, list_posts, update_post, publish_post,
    generate_rss_feed,
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
    repos = [
        {"github_id": 1, "owner": "org1", "name": "langchain", "full_name": "org1/langchain",
         "description": "LLM framework", "stars": 90000, "topics": ["llm"],
         "language": "Python", "category_primary": "frameworks"},
        {"github_id": 2, "owner": "org2", "name": "pytorch", "full_name": "org2/pytorch",
         "description": "Deep learning", "stars": 80000, "topics": ["ml"],
         "language": "Python", "category_primary": "frameworks"},
        {"github_id": 3, "owner": "org3", "name": "ollama", "full_name": "org3/ollama",
         "description": "Local LLMs", "stars": 50000, "topics": ["llm"],
         "language": "Go", "category_primary": "apps"},
    ]
    for repo in repos:
        insert_repo(repo, db_path)
    return db_path


# ======== Built With ========

class TestBuiltWith:
    def test_submit_project(self, seeded_db):
        pid = submit_project(1, "My App", "Built with langchain", "https://myapp.com", [1], path=seeded_db)
        assert pid > 0

    def test_get_project(self, seeded_db):
        pid = submit_project(1, "My App", "Built with langchain", "https://myapp.com", [1, 2], path=seeded_db)
        project = get_project(pid, seeded_db)
        assert project is not None
        assert project["title"] == "My App"
        assert project["status"] == "pending"
        assert set(project["repo_ids"]) == {1, 2}

    def test_get_nonexistent_project(self, seeded_db):
        assert get_project(9999, seeded_db) is None

    def test_list_projects_default_approved(self, seeded_db):
        pid = submit_project(1, "App1", "Desc", "https://a.com", [1], path=seeded_db)
        approve_project(pid, seeded_db)
        pid2 = submit_project(2, "App2", "Desc", "https://b.com", [2], path=seeded_db)
        # Only approved ones
        projects = list_projects(path=seeded_db)
        assert len(projects) == 1
        assert projects[0]["title"] == "App1"

    def test_list_projects_by_newest(self, seeded_db):
        for i in range(3):
            pid = submit_project(1, f"App{i}", "Desc", f"https://{i}.com", [1], path=seeded_db)
            approve_project(pid, seeded_db)
        projects = list_projects(sort="newest", path=seeded_db)
        assert len(projects) == 3

    def test_list_projects_for_repo(self, seeded_db):
        pid = submit_project(1, "App1", "Desc", "https://a.com", [1], path=seeded_db)
        approve_project(pid, seeded_db)
        pid2 = submit_project(2, "App2", "Desc", "https://b.com", [2], path=seeded_db)
        approve_project(pid2, seeded_db)
        # Only projects using repo 1
        projects = list_projects_for_repo(1, seeded_db)
        assert len(projects) == 1
        assert projects[0]["title"] == "App1"

    def test_approve_project(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        assert approve_project(pid, seeded_db) is True
        project = get_project(pid, seeded_db)
        assert project["status"] == "approved"

    def test_approve_already_approved(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        approve_project(pid, seeded_db)
        assert approve_project(pid, seeded_db) is False

    def test_reject_project(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        assert reject_project(pid, seeded_db) is True
        project = get_project(pid, seeded_db)
        assert project["status"] == "rejected"

    def test_reject_nonexistent(self, seeded_db):
        assert reject_project(9999, seeded_db) is False

    def test_submit_with_no_repos(self, seeded_db):
        pid = submit_project(1, "No Repos", "Desc", "https://a.com", [], path=seeded_db)
        project = get_project(pid, seeded_db)
        assert project["repo_ids"] == []

    def test_submit_with_screenshot(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1],
                             screenshot_url="https://img.com/shot.png", path=seeded_db)
        project = get_project(pid, seeded_db)
        assert project["screenshot_url"] == "https://img.com/shot.png"


# ======== Upvotes ========

class TestUpvotes:
    def test_toggle_upvote_adds(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        result = toggle_upvote(10, pid, seeded_db)
        assert result is True
        assert get_upvote_count(pid, seeded_db) == 1

    def test_toggle_upvote_removes(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        toggle_upvote(10, pid, seeded_db)
        result = toggle_upvote(10, pid, seeded_db)
        assert result is False
        assert get_upvote_count(pid, seeded_db) == 0

    def test_has_upvoted(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        assert has_upvoted(10, pid, seeded_db) is False
        toggle_upvote(10, pid, seeded_db)
        assert has_upvoted(10, pid, seeded_db) is True

    def test_multiple_users_upvote(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        toggle_upvote(10, pid, seeded_db)
        toggle_upvote(20, pid, seeded_db)
        toggle_upvote(30, pid, seeded_db)
        assert get_upvote_count(pid, seeded_db) == 3

    def test_idempotent_toggle(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        toggle_upvote(10, pid, seeded_db)  # add
        toggle_upvote(10, pid, seeded_db)  # remove
        toggle_upvote(10, pid, seeded_db)  # add again
        assert get_upvote_count(pid, seeded_db) == 1
        assert has_upvoted(10, pid, seeded_db) is True

    def test_get_upvote_count_nonexistent(self, seeded_db):
        assert get_upvote_count(9999, seeded_db) == 0


# ======== Comments ========

class TestComments:
    def test_add_comment(self, seeded_db):
        cid = add_comment(1, 1, "Great repo!", path=seeded_db)
        assert cid > 0

    def test_get_comments_threaded(self, seeded_db):
        c1 = add_comment(1, 1, "Top level", path=seeded_db)
        c2 = add_comment(2, 1, "Reply to c1", parent_id=c1, path=seeded_db)
        c3 = add_comment(3, 1, "Another top", path=seeded_db)
        comments = get_comments(1, path=seeded_db)
        assert len(comments) == 2  # two top-level
        parent = [c for c in comments if c["id"] == c1][0]
        assert len(parent["replies"]) == 1
        assert parent["replies"][0]["id"] == c2

    def test_update_comment_owner(self, seeded_db):
        cid = add_comment(1, 1, "Original", path=seeded_db)
        assert update_comment(cid, 1, "Updated", seeded_db) is True
        comments = get_comments(1, path=seeded_db)
        assert comments[0]["body"] == "Updated"

    def test_update_comment_wrong_user(self, seeded_db):
        cid = add_comment(1, 1, "Original", path=seeded_db)
        assert update_comment(cid, 2, "Hacked", seeded_db) is False

    def test_delete_comment_owner(self, seeded_db):
        cid = add_comment(1, 1, "To delete", path=seeded_db)
        assert delete_comment(cid, 1, seeded_db) is True
        comments = get_comments(1, path=seeded_db)
        assert len(comments) == 0

    def test_delete_comment_wrong_user(self, seeded_db):
        cid = add_comment(1, 1, "Mine", path=seeded_db)
        assert delete_comment(cid, 2, seeded_db) is False

    def test_flag_comment(self, seeded_db):
        cid = add_comment(1, 1, "Bad content", path=seeded_db)
        assert flag_comment(cid, seeded_db) is True

    def test_get_flagged_comments(self, seeded_db):
        c1 = add_comment(1, 1, "Normal", path=seeded_db)
        c2 = add_comment(2, 1, "Bad", path=seeded_db)
        flag_comment(c2, seeded_db)
        flagged = get_flagged_comments(seeded_db)
        assert len(flagged) == 1
        assert flagged[0]["id"] == c2

    def test_empty_comments(self, seeded_db):
        comments = get_comments(1, path=seeded_db)
        assert comments == []

    def test_comment_limit(self, seeded_db):
        for i in range(10):
            add_comment(1, 1, f"Comment {i}", path=seeded_db)
        comments = get_comments(1, limit=5, path=seeded_db)
        assert len(comments) == 5


# ======== Digest ========

class TestDigest:
    def test_generate_digest(self, seeded_db):
        digest = generate_digest(seeded_db)
        assert "generated_at" in digest
        assert "trending_repos" in digest
        assert "new_additions" in digest
        assert "top_projects" in digest
        assert len(digest["trending_repos"]) == 3  # we have 3 repos

    def test_generate_digest_with_built_with(self, seeded_db):
        pid = submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        approve_project(pid, seeded_db)
        digest = generate_digest(seeded_db)
        assert len(digest["top_projects"]) == 1

    def test_render_html(self, seeded_db):
        digest = generate_digest(seeded_db)
        html = render_digest_html(digest)
        assert "<html>" in html
        assert "Trending Repos" in html
        assert "org1/langchain" in html

    def test_render_markdown(self, seeded_db):
        digest = generate_digest(seeded_db)
        md = render_digest_markdown(digest)
        assert "# Reepo Weekly Digest" in md
        assert "org1/langchain" in md
        assert "## Trending Repos" in md

    def test_save_and_get_digest(self, seeded_db):
        digest = generate_digest(seeded_db)
        digest_id = save_digest(digest, seeded_db)
        assert digest_id > 0
        latest = get_latest_digest(seeded_db)
        assert latest is not None
        assert latest["issue_number"] == 1
        assert isinstance(latest["content"], dict)

    def test_save_increments_issue_number(self, seeded_db):
        d1 = generate_digest(seeded_db)
        save_digest(d1, seeded_db)
        d2 = generate_digest(seeded_db)
        save_digest(d2, seeded_db)
        latest = get_latest_digest(seeded_db)
        assert latest["issue_number"] == 2

    def test_get_latest_digest_empty(self, db_path):
        assert get_latest_digest(db_path) is None

    def test_render_empty_digest(self, db_path):
        digest = {"generated_at": "2024-01-01", "trending": [], "new_additions": [], "top_projects": []}
        html = render_digest_html(digest)
        assert "<html>" in html
        md = render_digest_markdown(digest)
        assert "# Reepo Weekly Digest" in md


# ======== Submissions ========

class TestSubmissions:
    def test_submit_repo(self, seeded_db):
        result = submit_repo(1, "https://github.com/neworg/newrepo", seeded_db)
        assert result["ok"] is True
        assert result["submission_id"] > 0

    def test_invalid_url(self, seeded_db):
        result = submit_repo(1, "not-a-url", seeded_db)
        assert result["ok"] is False
        assert "Invalid" in result["error"]

    def test_invalid_url_no_github(self, seeded_db):
        result = submit_repo(1, "https://gitlab.com/org/repo", seeded_db)
        assert result["ok"] is False

    def test_duplicate_submission(self, seeded_db):
        submit_repo(1, "https://github.com/neworg/newrepo", seeded_db)
        result = submit_repo(2, "https://github.com/neworg/newrepo", seeded_db)
        assert result["ok"] is False
        assert "Already submitted" in result["error"]

    def test_already_indexed(self, seeded_db):
        result = submit_repo(1, "https://github.com/org1/langchain", seeded_db)
        assert result["ok"] is False
        assert "already indexed" in result["error"]

    def test_list_pending(self, seeded_db):
        submit_repo(1, "https://github.com/a/b", seeded_db)
        submit_repo(2, "https://github.com/c/d", seeded_db)
        pending = list_pending_submissions(seeded_db)
        assert len(pending) == 2

    def test_approve_submission(self, seeded_db):
        result = submit_repo(1, "https://github.com/a/b", seeded_db)
        assert approve_submission(result["submission_id"], seeded_db) is True
        pending = list_pending_submissions(seeded_db)
        assert len(pending) == 0

    def test_reject_submission(self, seeded_db):
        result = submit_repo(1, "https://github.com/a/b", seeded_db)
        assert reject_submission(result["submission_id"], seeded_db) is True

    def test_approve_nonexistent(self, seeded_db):
        assert approve_submission(9999, seeded_db) is False

    def test_url_trailing_slash_normalized(self, seeded_db):
        result = submit_repo(1, "https://github.com/neworg/newrepo/", seeded_db)
        assert result["ok"] is True


# ======== Blog ========

class TestBlog:
    def test_create_post(self, db_path):
        pid = create_post("hello-world", "Hello World", "Content here", "admin", path=db_path)
        assert pid > 0

    def test_get_post(self, db_path):
        create_post("hello", "Hello", "Body", "admin", tags=["news", "ai"], path=db_path)
        post = get_post("hello", db_path)
        assert post is not None
        assert post["title"] == "Hello"
        assert post["tags"] == ["news", "ai"]

    def test_get_nonexistent_post(self, db_path):
        assert get_post("nope", db_path) is None

    def test_list_posts_published_only(self, db_path):
        create_post("draft", "Draft", "Body", "admin", path=db_path)
        create_post("pub", "Published", "Body", "admin", path=db_path)
        publish_post("pub", db_path)
        posts = list_posts(path=db_path)
        assert len(posts) == 1
        assert posts[0]["slug"] == "pub"

    def test_list_posts_by_tag(self, db_path):
        create_post("a", "A", "Body", "admin", tags=["news"], path=db_path)
        publish_post("a", db_path)
        create_post("b", "B", "Body", "admin", tags=["tech"], path=db_path)
        publish_post("b", db_path)
        posts = list_posts(tag="news", path=db_path)
        assert len(posts) == 1

    def test_update_post_title(self, db_path):
        create_post("up", "Old Title", "Body", "admin", path=db_path)
        assert update_post("up", title="New Title", path=db_path) is True
        post = get_post("up", db_path)
        assert post["title"] == "New Title"

    def test_update_post_body(self, db_path):
        create_post("up", "Title", "Old Body", "admin", path=db_path)
        assert update_post("up", body="New Body", path=db_path) is True
        post = get_post("up", db_path)
        assert post["body"] == "New Body"

    def test_update_post_tags(self, db_path):
        create_post("up", "Title", "Body", "admin", path=db_path)
        assert update_post("up", tags=["a", "b"], path=db_path) is True
        post = get_post("up", db_path)
        assert post["tags"] == ["a", "b"]

    def test_update_no_fields(self, db_path):
        create_post("up", "Title", "Body", "admin", path=db_path)
        assert update_post("up", path=db_path) is False

    def test_publish_post(self, db_path):
        create_post("pub", "Title", "Body", "admin", path=db_path)
        assert publish_post("pub", db_path) is True
        post = get_post("pub", db_path)
        assert post["published_at"] is not None

    def test_publish_already_published(self, db_path):
        create_post("pub", "Title", "Body", "admin", path=db_path)
        publish_post("pub", db_path)
        assert publish_post("pub", db_path) is False

    def test_generate_rss(self, db_path):
        create_post("a", "Post A", "Body A", "admin", path=db_path)
        publish_post("a", db_path)
        posts = list_posts(path=db_path)
        rss = generate_rss_feed(posts)
        assert '<?xml version="1.0"' in rss
        assert "<rss" in rss
        assert "Post A" in rss

    def test_rss_empty(self, db_path):
        rss = generate_rss_feed([])
        assert "<rss" in rss
        assert "<item>" not in rss


# ======== Admin ========

class TestAdmin:
    def test_admin_stats(self, seeded_db):
        stats = get_admin_stats(seeded_db)
        assert stats["total_repos"] == 3
        assert stats["pending_submissions"] == 0
        assert stats["flagged_comments"] == 0
        assert stats["pending_built_with"] == 0

    def test_admin_stats_with_data(self, seeded_db):
        submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        add_comment(1, 1, "Bad", path=seeded_db)
        flag_comment(1, seeded_db)
        submit_repo(1, "https://github.com/new/repo", seeded_db)
        stats = get_admin_stats(seeded_db)
        assert stats["pending_built_with"] == 1
        assert stats["flagged_comments"] == 1
        assert stats["pending_submissions"] == 1

    def test_moderation_queue(self, seeded_db):
        submit_project(1, "App", "Desc", "https://a.com", [1], path=seeded_db)
        cid = add_comment(1, 1, "Bad", path=seeded_db)
        flag_comment(cid, seeded_db)
        submit_repo(1, "https://github.com/new/repo", seeded_db)
        queue = get_moderation_queue(seeded_db)
        assert len(queue["pending_built_with"]) == 1
        assert len(queue["flagged_comments"]) == 1
        assert len(queue["pending_submissions"]) == 1

    def test_moderation_queue_empty(self, seeded_db):
        queue = get_moderation_queue(seeded_db)
        assert queue["pending_built_with"] == []
        assert queue["flagged_comments"] == []
        assert queue["pending_submissions"] == []

    def test_remove_comment(self, seeded_db):
        cid = add_comment(1, 1, "Remove me", path=seeded_db)
        assert remove_comment(cid, seeded_db) is True
        comments = get_comments(1, path=seeded_db)
        assert len(comments) == 0

    def test_remove_nonexistent_comment(self, seeded_db):
        assert remove_comment(9999, seeded_db) is False


# ======== API Integration ========

class TestCommunityAPI:
    """Integration tests for all Phase 5 API endpoints."""

    @pytest.fixture
    def client(self, seeded_db):
        from src.server import create_app
        from fastapi.testclient import TestClient
        app = create_app(seeded_db)
        return TestClient(app)

    # Built With
    def test_api_submit_project(self, client):
        resp = client.post("/api/built-with", json={
            "user_id": 1, "title": "App", "description": "Desc",
            "url": "https://a.com", "repo_ids": [1]
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    def test_api_list_projects(self, client):
        resp = client.get("/api/built-with")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_get_project(self, client):
        create_resp = client.post("/api/built-with", json={
            "user_id": 1, "title": "App", "description": "Desc",
            "url": "https://a.com", "repo_ids": [1]
        })
        pid = create_resp.json()["id"]
        resp = client.get(f"/api/built-with/{pid}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "App"

    def test_api_get_project_404(self, client):
        resp = client.get("/api/built-with/9999")
        assert resp.status_code == 404

    def test_api_toggle_upvote(self, client):
        create_resp = client.post("/api/built-with", json={
            "user_id": 1, "title": "App", "description": "Desc",
            "url": "https://a.com", "repo_ids": [1]
        })
        pid = create_resp.json()["id"]
        resp = client.post(f"/api/built-with/{pid}/upvote?user_id=10")
        assert resp.status_code == 200
        assert resp.json()["upvoted"] is True

    # Comments
    def test_api_get_comments(self, client):
        resp = client.get("/api/repos/org1/langchain/comments")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_add_comment(self, client):
        resp = client.post("/api/repos/org1/langchain/comments", json={
            "user_id": 1, "body": "Great repo!"
        })
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_api_comments_repo_404(self, client):
        resp = client.get("/api/repos/nope/nope/comments")
        assert resp.status_code == 404

    # Repo Built With
    def test_api_repo_built_with(self, client):
        resp = client.get("/api/repos/org1/langchain/built-with")
        assert resp.status_code == 200

    def test_api_repo_built_with_404(self, client):
        resp = client.get("/api/repos/nope/nope/built-with")
        assert resp.status_code == 404

    # Submissions
    def test_api_submit_repo(self, client):
        resp = client.post("/api/submissions", json={
            "user_id": 1, "github_url": "https://github.com/new/repo"
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    def test_api_submit_invalid_url(self, client):
        resp = client.post("/api/submissions", json={
            "user_id": 1, "github_url": "not-valid"
        })
        assert resp.status_code == 400

    # Digest
    def test_api_digest_latest_404(self, client):
        resp = client.get("/api/digest/latest")
        assert resp.status_code == 404

    def test_api_digest_latest(self, client, seeded_db):
        digest = generate_digest(seeded_db)
        save_digest(digest, seeded_db)
        resp = client.get("/api/digest/latest")
        assert resp.status_code == 200

    # Admin
    def test_api_admin_stats(self, client):
        resp = client.get("/api/admin/stats")
        assert resp.status_code == 200
        assert "total_repos" in resp.json()

    def test_api_admin_moderation(self, client):
        resp = client.get("/api/admin/moderation")
        assert resp.status_code == 200

    def test_api_admin_approve_built_with(self, client):
        create_resp = client.post("/api/built-with", json={
            "user_id": 1, "title": "App", "description": "Desc",
            "url": "https://a.com", "repo_ids": [1]
        })
        pid = create_resp.json()["id"]
        resp = client.post(f"/api/admin/built-with/{pid}/approve")
        assert resp.status_code == 200

    def test_api_admin_reject_built_with(self, client):
        create_resp = client.post("/api/built-with", json={
            "user_id": 1, "title": "App", "description": "Desc",
            "url": "https://a.com", "repo_ids": [1]
        })
        pid = create_resp.json()["id"]
        resp = client.post(f"/api/admin/built-with/{pid}/reject")
        assert resp.status_code == 200

    def test_api_admin_approve_submission(self, client):
        sub_resp = client.post("/api/submissions", json={
            "user_id": 1, "github_url": "https://github.com/new/repo"
        })
        sid = sub_resp.json()["id"]
        resp = client.post(f"/api/admin/submissions/{sid}/approve")
        assert resp.status_code == 200

    def test_api_admin_reject_submission(self, client):
        sub_resp = client.post("/api/submissions", json={
            "user_id": 1, "github_url": "https://github.com/new/repo"
        })
        sid = sub_resp.json()["id"]
        resp = client.post(f"/api/admin/submissions/{sid}/reject")
        assert resp.status_code == 200

    def test_api_admin_remove_comment(self, client):
        comment_resp = client.post("/api/repos/org1/langchain/comments", json={
            "user_id": 1, "body": "Remove me"
        })
        cid = comment_resp.json()["id"]
        resp = client.post(f"/api/admin/comments/{cid}/remove")
        assert resp.status_code == 200

    def test_api_admin_remove_comment_404(self, client):
        resp = client.post("/api/admin/comments/9999/remove")
        assert resp.status_code == 404

    # Blog
    def test_api_blog_list(self, client):
        resp = client.get("/api/blog")
        assert resp.status_code == 200

    def test_api_blog_create(self, client):
        resp = client.post("/api/blog", json={
            "slug": "test", "title": "Test", "body": "Content", "author": "admin"
        })
        assert resp.status_code == 200
        assert resp.json()["slug"] == "test"

    def test_api_blog_get(self, client, db_path):
        create_post("hello", "Hello", "Body", "admin", path=db_path)
        resp = client.get("/api/blog/hello")
        assert resp.status_code == 200

    def test_api_blog_get_404(self, client):
        resp = client.get("/api/blog/nope")
        assert resp.status_code == 404

    def test_api_blog_rss(self, client, db_path):
        create_post("rss-test", "RSS Test", "Body", "admin", path=db_path)
        publish_post("rss-test", db_path)
        resp = client.get("/api/blog/rss")
        assert resp.status_code == 200
        assert "xml" in resp.headers["content-type"]
