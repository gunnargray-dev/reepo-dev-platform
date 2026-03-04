"""Tests for auth DB — users, sessions, and API keys CRUD."""
import os
import tempfile

import pytest

from src.auth.db import (
    init_auth_db,
    create_user, get_user_by_id, get_user_by_username, get_user_by_github_id,
    update_user, delete_user,
    create_session, get_session_by_token, get_session_by_refresh,
    delete_session, delete_user_sessions,
    create_api_key, get_api_keys_for_user, get_api_key,
    delete_api_key, increment_api_key_usage, reset_api_key_usage,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_auth_db(path)
    yield path
    os.unlink(path)


# --- Users ---

class TestUsersCRUD:
    def test_create_and_get_user(self, db_path):
        uid = create_user("alice", db_path, github_id=100, email="alice@test.com")
        assert uid > 0
        user = get_user_by_id(uid, db_path)
        assert user["username"] == "alice"
        assert user["github_id"] == 100
        assert user["email"] == "alice@test.com"

    def test_get_user_by_username(self, db_path):
        create_user("bob", db_path)
        user = get_user_by_username("bob", db_path)
        assert user is not None
        assert user["username"] == "bob"

    def test_get_user_by_github_id(self, db_path):
        create_user("charlie", db_path, github_id=200)
        user = get_user_by_github_id(200, db_path)
        assert user is not None
        assert user["username"] == "charlie"

    def test_get_nonexistent_user(self, db_path):
        assert get_user_by_id(999, db_path) is None
        assert get_user_by_username("nonexistent", db_path) is None
        assert get_user_by_github_id(999, db_path) is None

    def test_update_user(self, db_path):
        uid = create_user("dave", db_path)
        ok = update_user(uid, db_path, display_name="Dave D.", bio="hello")
        assert ok is True
        user = get_user_by_id(uid, db_path)
        assert user["display_name"] == "Dave D."
        assert user["bio"] == "hello"

    def test_update_user_no_fields(self, db_path):
        uid = create_user("eve", db_path)
        assert update_user(uid, db_path) is False

    def test_update_user_disallowed_field(self, db_path):
        uid = create_user("frank", db_path)
        assert update_user(uid, db_path, id=999) is False

    def test_delete_user(self, db_path):
        uid = create_user("grace", db_path)
        assert delete_user(uid, db_path) is True
        assert get_user_by_id(uid, db_path) is None

    def test_delete_nonexistent_user(self, db_path):
        assert delete_user(999, db_path) is False

    def test_unique_username(self, db_path):
        create_user("unique", db_path)
        with pytest.raises(Exception):
            create_user("unique", db_path)

    def test_unique_github_id(self, db_path):
        create_user("user1", db_path, github_id=300)
        with pytest.raises(Exception):
            create_user("user2", db_path, github_id=300)

    def test_create_user_with_all_fields(self, db_path):
        uid = create_user(
            "full", db_path,
            github_id=400, email="full@test.com",
            display_name="Full User", avatar_url="https://example.com/avatar.png",
            bio="A full user"
        )
        user = get_user_by_id(uid, db_path)
        assert user["avatar_url"] == "https://example.com/avatar.png"
        assert user["is_pro"] == 0

    def test_update_is_pro(self, db_path):
        uid = create_user("pro_user", db_path)
        update_user(uid, db_path, is_pro=True)
        user = get_user_by_id(uid, db_path)
        assert user["is_pro"] == 1


# --- Sessions ---

class TestSessionsCRUD:
    def test_create_and_get_session(self, db_path):
        uid = create_user("sess_user", db_path)
        sid = create_session(uid, "tok_abc", "ref_abc", "2099-01-01T00:00:00", db_path)
        assert sid > 0
        sess = get_session_by_token("tok_abc", db_path)
        assert sess["user_id"] == uid
        assert sess["refresh_token"] == "ref_abc"

    def test_get_session_by_refresh(self, db_path):
        uid = create_user("ref_user", db_path)
        create_session(uid, "tok_def", "ref_def", "2099-01-01T00:00:00", db_path)
        sess = get_session_by_refresh("ref_def", db_path)
        assert sess["token"] == "tok_def"

    def test_get_nonexistent_session(self, db_path):
        assert get_session_by_token("nonexistent", db_path) is None
        assert get_session_by_refresh("nonexistent", db_path) is None

    def test_delete_session(self, db_path):
        uid = create_user("del_sess_user", db_path)
        create_session(uid, "tok_del", "ref_del", "2099-01-01T00:00:00", db_path)
        assert delete_session("tok_del", db_path) is True
        assert get_session_by_token("tok_del", db_path) is None

    def test_delete_nonexistent_session(self, db_path):
        assert delete_session("nonexistent", db_path) is False

    def test_delete_user_sessions(self, db_path):
        uid = create_user("multi_sess", db_path)
        create_session(uid, "tok1", "ref1", "2099-01-01T00:00:00", db_path)
        create_session(uid, "tok2", "ref2", "2099-01-01T00:00:00", db_path)
        count = delete_user_sessions(uid, db_path)
        assert count == 2
        assert get_session_by_token("tok1", db_path) is None
        assert get_session_by_token("tok2", db_path) is None


# --- API Keys ---

class TestAPIKeysCRUD:
    def test_create_api_key(self, db_path):
        uid = create_user("key_user", db_path)
        result = create_api_key(uid, "My Key", db_path)
        assert result["key"].startswith("rp_")
        assert result["name"] == "My Key"
        assert result["daily_limit"] == 100

    def test_get_api_keys_for_user(self, db_path):
        uid = create_user("keys_user", db_path)
        create_api_key(uid, "Key 1", db_path)
        create_api_key(uid, "Key 2", db_path)
        keys = get_api_keys_for_user(uid, db_path)
        assert len(keys) == 2

    def test_get_api_key(self, db_path):
        uid = create_user("get_key_user", db_path)
        result = create_api_key(uid, "Test Key", db_path)
        fetched = get_api_key(result["key"], db_path)
        assert fetched is not None
        assert fetched["name"] == "Test Key"

    def test_get_nonexistent_key(self, db_path):
        assert get_api_key("rp_nonexistent", db_path) is None

    def test_delete_api_key(self, db_path):
        uid = create_user("del_key_user", db_path)
        result = create_api_key(uid, "Del Key", db_path)
        assert delete_api_key(result["id"], uid, db_path) is True
        assert get_api_key(result["key"], db_path) is None

    def test_delete_key_wrong_user(self, db_path):
        uid = create_user("owner", db_path)
        uid2 = create_user("other", db_path)
        result = create_api_key(uid, "Key", db_path)
        assert delete_api_key(result["id"], uid2, db_path) is False

    def test_increment_usage(self, db_path):
        uid = create_user("usage_user", db_path)
        result = create_api_key(uid, "Usage Key", db_path)
        assert increment_api_key_usage(result["key"], db_path) is True
        key = get_api_key(result["key"], db_path)
        assert key["requests_today"] == 1

    def test_reset_usage(self, db_path):
        uid = create_user("reset_user", db_path)
        result = create_api_key(uid, "Reset Key", db_path)
        increment_api_key_usage(result["key"], db_path)
        assert reset_api_key_usage(result["key"], db_path) is True
        key = get_api_key(result["key"], db_path)
        assert key["requests_today"] == 0

    def test_custom_daily_limit(self, db_path):
        uid = create_user("limit_user", db_path)
        result = create_api_key(uid, "Limited", db_path, daily_limit=500)
        assert result["daily_limit"] == 500
