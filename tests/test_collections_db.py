"""Tests for collections DB — collections, bookmarks, follows, notifications."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.auth.db import init_auth_db, create_user
from src.collections.db import (
    init_collections_db,
    create_collection, get_collection, list_collections,
    update_collection, delete_collection,
    add_repo_to_collection, remove_repo_from_collection, get_collection_repos,
    add_bookmark, remove_bookmark, get_bookmarks,
    follow_user, unfollow_user, get_followers, get_following,
    create_notification, get_notifications, mark_notification_read, mark_all_notifications_read,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_auth_db(path)
    init_collections_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def user_and_repo(db_path):
    uid = create_user("testuser", db_path, github_id=1)
    rid = insert_repo({
        "github_id": 100, "owner": "org", "name": "repo",
        "full_name": "org/repo", "stars": 500, "reepo_score": 75,
    }, db_path)
    return uid, rid


# --- Collections ---

class TestCollectionsCRUD:
    def test_create_and_get(self, db_path):
        uid = create_user("coll_user", db_path)
        cid = create_collection(uid, "My List", "my-list", db_path, description="Faves")
        assert cid > 0
        coll = get_collection(cid, db_path)
        assert coll["name"] == "My List"
        assert coll["slug"] == "my-list"
        assert coll["is_public"] == 1

    def test_list_collections(self, db_path):
        uid = create_user("list_user", db_path)
        create_collection(uid, "A", "a", db_path)
        create_collection(uid, "B", "b", db_path)
        colls = list_collections(uid, db_path)
        assert len(colls) == 2

    def test_update_collection(self, db_path):
        uid = create_user("upd_user", db_path)
        cid = create_collection(uid, "Old", "old", db_path)
        ok = update_collection(cid, uid, db_path, name="New", is_public=False)
        assert ok is True
        coll = get_collection(cid, db_path)
        assert coll["name"] == "New"
        assert coll["is_public"] == 0

    def test_update_wrong_user(self, db_path):
        uid1 = create_user("owner1", db_path)
        uid2 = create_user("other1", db_path)
        cid = create_collection(uid1, "Mine", "mine", db_path)
        assert update_collection(cid, uid2, db_path, name="Stolen") is False

    def test_delete_collection(self, db_path):
        uid = create_user("del_user", db_path)
        cid = create_collection(uid, "Temp", "temp", db_path)
        assert delete_collection(cid, uid, db_path) is True
        assert get_collection(cid, db_path) is None

    def test_delete_wrong_user(self, db_path):
        uid1 = create_user("del_own", db_path)
        uid2 = create_user("del_other", db_path)
        cid = create_collection(uid1, "Mine2", "mine2", db_path)
        assert delete_collection(cid, uid2, db_path) is False

    def test_get_nonexistent(self, db_path):
        assert get_collection(999, db_path) is None

    def test_private_collection(self, db_path):
        uid = create_user("priv_user", db_path)
        cid = create_collection(uid, "Secret", "secret", db_path, is_public=False)
        coll = get_collection(cid, db_path)
        assert coll["is_public"] == 0


# --- Collection Repos ---

class TestCollectionRepos:
    def test_add_and_get_repos(self, db_path, user_and_repo):
        uid, rid = user_and_repo
        cid = create_collection(uid, "Starred", "starred", db_path)
        assert add_repo_to_collection(cid, rid, db_path) is True
        repos = get_collection_repos(cid, db_path)
        assert len(repos) == 1

    def test_add_duplicate_repo(self, db_path, user_and_repo):
        uid, rid = user_and_repo
        cid = create_collection(uid, "Dup", "dup", db_path)
        add_repo_to_collection(cid, rid, db_path)
        assert add_repo_to_collection(cid, rid, db_path) is False

    def test_remove_repo(self, db_path, user_and_repo):
        uid, rid = user_and_repo
        cid = create_collection(uid, "Rem", "rem", db_path)
        add_repo_to_collection(cid, rid, db_path)
        assert remove_repo_from_collection(cid, rid, db_path) is True
        assert len(get_collection_repos(cid, db_path)) == 0

    def test_remove_nonexistent(self, db_path, user_and_repo):
        uid, rid = user_and_repo
        cid = create_collection(uid, "Empty", "empty", db_path)
        assert remove_repo_from_collection(cid, rid, db_path) is False

    def test_delete_collection_removes_repos(self, db_path, user_and_repo):
        uid, rid = user_and_repo
        cid = create_collection(uid, "Del", "del", db_path)
        add_repo_to_collection(cid, rid, db_path)
        delete_collection(cid, uid, db_path)
        assert get_collection_repos(cid, db_path) == []


# --- Bookmarks ---

class TestBookmarks:
    def test_add_and_get_bookmark(self, db_path, user_and_repo):
        uid, rid = user_and_repo
        assert add_bookmark(uid, rid, db_path) is True
        bms = get_bookmarks(uid, db_path)
        assert len(bms) == 1

    def test_duplicate_bookmark(self, db_path, user_and_repo):
        uid, rid = user_and_repo
        add_bookmark(uid, rid, db_path)
        assert add_bookmark(uid, rid, db_path) is False

    def test_remove_bookmark(self, db_path, user_and_repo):
        uid, rid = user_and_repo
        add_bookmark(uid, rid, db_path)
        assert remove_bookmark(uid, rid, db_path) is True
        assert len(get_bookmarks(uid, db_path)) == 0

    def test_remove_nonexistent_bookmark(self, db_path, user_and_repo):
        uid, rid = user_and_repo
        assert remove_bookmark(uid, rid, db_path) is False


# --- Follows ---

class TestFollows:
    def test_follow_and_get_followers(self, db_path):
        uid1 = create_user("follower1", db_path)
        uid2 = create_user("followed1", db_path)
        assert follow_user(uid1, uid2, db_path) is True
        followers = get_followers(uid2, db_path)
        assert len(followers) == 1

    def test_get_following(self, db_path):
        uid1 = create_user("follower2", db_path)
        uid2 = create_user("followed2", db_path)
        follow_user(uid1, uid2, db_path)
        following = get_following(uid1, db_path)
        assert len(following) == 1

    def test_self_follow_prevented(self, db_path):
        uid = create_user("narcissist", db_path)
        assert follow_user(uid, uid, db_path) is False

    def test_duplicate_follow(self, db_path):
        uid1 = create_user("dup_f1", db_path)
        uid2 = create_user("dup_f2", db_path)
        follow_user(uid1, uid2, db_path)
        assert follow_user(uid1, uid2, db_path) is False

    def test_unfollow(self, db_path):
        uid1 = create_user("unf1", db_path)
        uid2 = create_user("unf2", db_path)
        follow_user(uid1, uid2, db_path)
        assert unfollow_user(uid1, uid2, db_path) is True
        assert len(get_followers(uid2, db_path)) == 0

    def test_unfollow_not_following(self, db_path):
        uid1 = create_user("notf1", db_path)
        uid2 = create_user("notf2", db_path)
        assert unfollow_user(uid1, uid2, db_path) is False


# --- Notifications ---

class TestNotifications:
    def test_create_and_get(self, db_path):
        uid = create_user("notif_user", db_path)
        nid = create_notification(uid, "follow", "Someone followed you", db_path)
        assert nid > 0
        notifs = get_notifications(uid, db_path)
        assert len(notifs) == 1
        assert notifs[0]["message"] == "Someone followed you"
        assert notifs[0]["is_read"] == 0

    def test_with_data(self, db_path):
        uid = create_user("data_user", db_path)
        create_notification(uid, "repo", "New repo", db_path, data={"repo_id": 42})
        notifs = get_notifications(uid, db_path)
        assert notifs[0]["data"] == {"repo_id": 42}

    def test_unread_only(self, db_path):
        uid = create_user("unread_user", db_path)
        nid1 = create_notification(uid, "a", "Msg A", db_path)
        create_notification(uid, "b", "Msg B", db_path)
        mark_notification_read(nid1, uid, db_path)
        unread = get_notifications(uid, db_path, unread_only=True)
        assert len(unread) == 1
        assert unread[0]["message"] == "Msg B"

    def test_mark_read(self, db_path):
        uid = create_user("mark_user", db_path)
        nid = create_notification(uid, "x", "Read me", db_path)
        assert mark_notification_read(nid, uid, db_path) is True
        notifs = get_notifications(uid, db_path)
        assert notifs[0]["is_read"] == 1

    def test_mark_read_wrong_user(self, db_path):
        uid1 = create_user("mark_own", db_path)
        uid2 = create_user("mark_other", db_path)
        nid = create_notification(uid1, "x", "Private", db_path)
        assert mark_notification_read(nid, uid2, db_path) is False

    def test_mark_all_read(self, db_path):
        uid = create_user("all_read", db_path)
        create_notification(uid, "a", "1", db_path)
        create_notification(uid, "b", "2", db_path)
        create_notification(uid, "c", "3", db_path)
        count = mark_all_notifications_read(uid, db_path)
        assert count == 3
        unread = get_notifications(uid, db_path, unread_only=True)
        assert len(unread) == 0
