"""Tests for auth, collections, bookmarks, users, and API keys API endpoints."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.db import init_db, insert_repo
from src.auth.db import init_auth_db, create_user, create_session
from src.auth.jwt_auth import create_access_token, create_refresh_token
from src.auth import github_oauth
from src.collections.db import init_collections_db, create_notification
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
def auth_client(client):
    """Client with a pre-created user and valid access token."""
    c, path = client
    uid = create_user("testuser", path, github_id=1, email="test@example.com",
                       display_name="Test User")
    token = create_access_token(uid)
    headers = {"Authorization": f"Bearer {token}"}
    return c, path, uid, token, headers


@pytest.fixture
def seeded_auth_client(auth_client):
    """Auth client with a repo inserted."""
    c, path, uid, token, headers = auth_client
    rid = insert_repo({
        "github_id": 100, "owner": "org", "name": "repo",
        "full_name": "org/repo", "stars": 500, "reepo_score": 75,
    }, path)
    return c, path, uid, token, headers, rid


# --- Auth API ---

class TestAuthGithub:
    def test_get_auth_url(self, client):
        c, _ = client
        resp = c.get("/api/auth/github")
        assert resp.status_code == 200
        assert "auth_url" in resp.json()
        assert "github.com" in resp.json()["auth_url"]

    def test_get_auth_url_with_state(self, client):
        c, _ = client
        resp = c.get("/api/auth/github?state=mystate")
        assert resp.status_code == 200
        assert "mystate" in resp.json()["auth_url"]


class TestAuthCallback:
    def test_callback_success(self, client, monkeypatch):
        c, path = client

        def mock_exchange(code):
            return {"access_token": "gho_test"}

        def mock_get_user(token):
            return {"id": 999, "login": "newuser", "name": "New User",
                    "email": "new@test.com", "avatar_url": None, "bio": None}

        monkeypatch.setattr(github_oauth, "exchange_code", mock_exchange)
        monkeypatch.setattr(github_oauth, "get_github_user", mock_get_user)

        resp = c.get("/api/auth/github/callback?code=test_code")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_callback_existing_user(self, client, monkeypatch):
        c, path = client
        # Pre-create user
        create_user("existing", path, github_id=888)

        def mock_exchange(code):
            return {"access_token": "gho_test"}

        def mock_get_user(token):
            return {"id": 888, "login": "existing"}

        monkeypatch.setattr(github_oauth, "exchange_code", mock_exchange)
        monkeypatch.setattr(github_oauth, "get_github_user", mock_get_user)

        resp = c.get("/api/auth/github/callback?code=test_code")
        assert resp.status_code == 200

    def test_callback_exchange_fails(self, client, monkeypatch):
        c, _ = client

        def mock_exchange(code):
            raise ValueError("bad code")

        monkeypatch.setattr(github_oauth, "exchange_code", mock_exchange)
        resp = c.get("/api/auth/github/callback?code=bad")
        assert resp.status_code == 400


class TestAuthRefresh:
    def test_refresh_token(self, client):
        c, path = client
        uid = create_user("refresh_user", path)
        access = create_access_token(uid)
        refresh = create_refresh_token(uid)
        create_session(uid, access, refresh, "2099-01-01T00:00:00", path)

        resp = c.post("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_no_token(self, client):
        c, _ = client
        resp = c.post("/api/auth/refresh")
        assert resp.status_code == 401

    def test_refresh_with_access_token_fails(self, client):
        c, path = client
        uid = create_user("bad_refresh", path)
        access = create_access_token(uid)
        resp = c.post("/api/auth/refresh", headers={"Authorization": f"Bearer {access}"})
        assert resp.status_code == 401


class TestAuthLogout:
    def test_logout(self, client):
        c, path = client
        uid = create_user("logout_user", path)
        access = create_access_token(uid)
        refresh = create_refresh_token(uid)
        create_session(uid, access, refresh, "2099-01-01T00:00:00", path)

        resp = c.post("/api/auth/logout", headers={"Authorization": f"Bearer {access}"})
        assert resp.status_code == 200
        assert resp.json()["logged_out"] is True

    def test_logout_no_token(self, client):
        c, _ = client
        resp = c.post("/api/auth/logout")
        assert resp.status_code == 401


class TestAuthMe:
    def test_get_me(self, auth_client):
        c, path, uid, token, headers = auth_client
        resp = c.get("/api/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    def test_get_me_no_token(self, client):
        c, _ = client
        resp = c.get("/api/auth/me")
        assert resp.status_code == 401


# --- Collections API ---

class TestCollectionsAPI:
    def test_create_collection(self, auth_client):
        c, path, uid, token, headers = auth_client
        resp = c.post("/api/collections", json={
            "name": "My List", "slug": "my-list", "description": "Faves"
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "My List"

    def test_list_collections(self, auth_client):
        c, path, uid, token, headers = auth_client
        c.post("/api/collections", json={"name": "A", "slug": "a"}, headers=headers)
        resp = c.get("/api/collections", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_collection(self, auth_client):
        c, path, uid, token, headers = auth_client
        create_resp = c.post("/api/collections", json={"name": "X", "slug": "x"}, headers=headers)
        cid = create_resp.json()["id"]
        resp = c.get(f"/api/collections/{cid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "X"

    def test_get_nonexistent_collection(self, auth_client):
        c, path, uid, token, headers = auth_client
        resp = c.get("/api/collections/999")
        assert resp.status_code == 404

    def test_update_collection(self, auth_client):
        c, path, uid, token, headers = auth_client
        create_resp = c.post("/api/collections", json={"name": "Old", "slug": "old"}, headers=headers)
        cid = create_resp.json()["id"]
        resp = c.put(f"/api/collections/{cid}", json={"name": "New"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["updated"] is True

    def test_delete_collection(self, auth_client):
        c, path, uid, token, headers = auth_client
        create_resp = c.post("/api/collections", json={"name": "Del", "slug": "del"}, headers=headers)
        cid = create_resp.json()["id"]
        resp = c.delete(f"/api/collections/{cid}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_create_requires_auth(self, client):
        c, _ = client
        resp = c.post("/api/collections", json={"name": "X", "slug": "x"})
        assert resp.status_code == 401


class TestCollectionReposAPI:
    def test_add_repo(self, seeded_auth_client):
        c, path, uid, token, headers, rid = seeded_auth_client
        create_resp = c.post("/api/collections", json={"name": "R", "slug": "r"}, headers=headers)
        cid = create_resp.json()["id"]
        resp = c.post(f"/api/collections/{cid}/repos", json={"repo_id": rid}, headers=headers)
        assert resp.status_code == 200

    def test_list_repos(self, seeded_auth_client):
        c, path, uid, token, headers, rid = seeded_auth_client
        create_resp = c.post("/api/collections", json={"name": "L", "slug": "l"}, headers=headers)
        cid = create_resp.json()["id"]
        c.post(f"/api/collections/{cid}/repos", json={"repo_id": rid}, headers=headers)
        resp = c.get(f"/api/collections/{cid}/repos")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_remove_repo(self, seeded_auth_client):
        c, path, uid, token, headers, rid = seeded_auth_client
        create_resp = c.post("/api/collections", json={"name": "D", "slug": "d"}, headers=headers)
        cid = create_resp.json()["id"]
        c.post(f"/api/collections/{cid}/repos", json={"repo_id": rid}, headers=headers)
        resp = c.delete(f"/api/collections/{cid}/repos/{rid}", headers=headers)
        assert resp.status_code == 200

    def test_add_duplicate_repo(self, seeded_auth_client):
        c, path, uid, token, headers, rid = seeded_auth_client
        create_resp = c.post("/api/collections", json={"name": "Dup", "slug": "dup"}, headers=headers)
        cid = create_resp.json()["id"]
        c.post(f"/api/collections/{cid}/repos", json={"repo_id": rid}, headers=headers)
        resp = c.post(f"/api/collections/{cid}/repos", json={"repo_id": rid}, headers=headers)
        assert resp.status_code == 409


# --- Bookmarks API ---

class TestBookmarksAPI:
    def test_add_bookmark(self, seeded_auth_client):
        c, path, uid, token, headers, rid = seeded_auth_client
        resp = c.post(f"/api/bookmarks/{rid}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["bookmarked"] is True

    def test_list_bookmarks(self, seeded_auth_client):
        c, path, uid, token, headers, rid = seeded_auth_client
        c.post(f"/api/bookmarks/{rid}", headers=headers)
        resp = c.get("/api/bookmarks", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_remove_bookmark(self, seeded_auth_client):
        c, path, uid, token, headers, rid = seeded_auth_client
        c.post(f"/api/bookmarks/{rid}", headers=headers)
        resp = c.delete(f"/api/bookmarks/{rid}", headers=headers)
        assert resp.status_code == 200

    def test_duplicate_bookmark(self, seeded_auth_client):
        c, path, uid, token, headers, rid = seeded_auth_client
        c.post(f"/api/bookmarks/{rid}", headers=headers)
        resp = c.post(f"/api/bookmarks/{rid}", headers=headers)
        assert resp.status_code == 409

    def test_bookmarks_require_auth(self, client):
        c, _ = client
        resp = c.get("/api/bookmarks")
        assert resp.status_code == 401


# --- Users API ---

class TestUsersAPI:
    def test_get_profile_by_username(self, auth_client):
        c, path, uid, token, headers = auth_client
        resp = c.get("/api/users/testuser")
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"
        assert "email" not in resp.json()  # email excluded from public

    def test_get_nonexistent_user(self, client):
        c, _ = client
        resp = c.get("/api/users/nonexistent")
        assert resp.status_code == 404

    def test_update_profile(self, auth_client):
        c, path, uid, token, headers = auth_client
        resp = c.put("/api/users/me", json={"display_name": "Updated"}, headers=headers)
        assert resp.status_code == 200

    def test_update_requires_auth(self, client):
        c, _ = client
        resp = c.put("/api/users/me", json={"display_name": "X"})
        assert resp.status_code == 401


class TestFollowAPI:
    def test_follow_user(self, auth_client):
        c, path, uid, token, headers = auth_client
        uid2 = create_user("followee", path)
        resp = c.post(f"/api/users/{uid2}/follow", headers=headers)
        assert resp.status_code == 200

    def test_self_follow_prevented(self, auth_client):
        c, path, uid, token, headers = auth_client
        resp = c.post(f"/api/users/{uid}/follow", headers=headers)
        assert resp.status_code == 400

    def test_unfollow_user(self, auth_client):
        c, path, uid, token, headers = auth_client
        uid2 = create_user("unfollowee", path)
        c.post(f"/api/users/{uid2}/follow", headers=headers)
        resp = c.delete(f"/api/users/{uid2}/follow", headers=headers)
        assert resp.status_code == 200

    def test_get_followers(self, auth_client):
        c, path, uid, token, headers = auth_client
        uid2 = create_user("target", path)
        c.post(f"/api/users/{uid2}/follow", headers=headers)
        resp = c.get(f"/api/users/{uid2}/followers")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_get_following(self, auth_client):
        c, path, uid, token, headers = auth_client
        uid2 = create_user("target2", path)
        c.post(f"/api/users/{uid2}/follow", headers=headers)
        resp = c.get(f"/api/users/{uid}/following")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_duplicate_follow(self, auth_client):
        c, path, uid, token, headers = auth_client
        uid2 = create_user("dup_target", path)
        c.post(f"/api/users/{uid2}/follow", headers=headers)
        resp = c.post(f"/api/users/{uid2}/follow", headers=headers)
        assert resp.status_code == 409


class TestNotificationsAPI:
    def test_get_notifications(self, auth_client):
        c, path, uid, token, headers = auth_client
        create_notification(uid, "test", "Hello", path)
        resp = c.get("/api/users/me/notifications", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_mark_notification_read(self, auth_client):
        c, path, uid, token, headers = auth_client
        nid = create_notification(uid, "test", "Read me", path)
        resp = c.post(f"/api/users/me/notifications/{nid}/read", headers=headers)
        assert resp.status_code == 200

    def test_mark_all_read(self, auth_client):
        c, path, uid, token, headers = auth_client
        create_notification(uid, "a", "1", path)
        create_notification(uid, "b", "2", path)
        resp = c.post("/api/users/me/notifications/read-all", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["marked_read"] == 2

    def test_notifications_require_auth(self, client):
        c, _ = client
        resp = c.get("/api/users/me/notifications")
        # This will match /api/users/{username} with username="me" -> 404
        # because it requires auth via that route. But since the /me/notifications
        # route is registered, let's check it properly.
        # The route ordering means /me routes should match before /{username}
        assert resp.status_code == 401


# --- API Keys ---

class TestAPIKeysAPI:
    def test_create_key(self, auth_client):
        c, path, uid, token, headers = auth_client
        resp = c.post("/api/keys", json={"name": "My Key"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"].startswith("rp_")
        assert data["name"] == "My Key"

    def test_list_keys(self, auth_client):
        c, path, uid, token, headers = auth_client
        c.post("/api/keys", json={"name": "Key1"}, headers=headers)
        c.post("/api/keys", json={"name": "Key2"}, headers=headers)
        resp = c.get("/api/keys", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_delete_key(self, auth_client):
        c, path, uid, token, headers = auth_client
        create_resp = c.post("/api/keys", json={"name": "DelKey"}, headers=headers)
        key_id = create_resp.json()["id"]
        resp = c.delete(f"/api/keys/{key_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_nonexistent_key(self, auth_client):
        c, path, uid, token, headers = auth_client
        resp = c.delete("/api/keys/999", headers=headers)
        assert resp.status_code == 404

    def test_keys_require_auth(self, client):
        c, _ = client
        resp = c.get("/api/keys")
        assert resp.status_code == 401

    def test_custom_daily_limit(self, auth_client):
        c, path, uid, token, headers = auth_client
        resp = c.post("/api/keys", json={"name": "Custom", "daily_limit": 500}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["daily_limit"] == 500
