"""Tests for the Reepo newsletter — subscribe, unsubscribe, digest generation."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.monetization.db import init_monetization_db
from src.monetization.newsletter import (
    subscribe,
    unsubscribe,
    get_subscriber_count,
    build_weekly_digest,
    get_latest_newsletter,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_monetization_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def seeded_db(db_path):
    for i in range(5):
        insert_repo({
            "github_id": 50000 + i,
            "owner": "news-org",
            "name": f"news-repo-{i}",
            "full_name": f"news-org/news-repo-{i}",
            "description": f"Newsletter test repo {i}",
            "stars": 500 + i * 100,
            "language": "Python",
        }, db_path)
    return db_path


class TestSubscribe:
    def test_subscribe_valid_email(self, db_path):
        assert subscribe("user@example.com", path=db_path) is True

    def test_subscribe_invalid_email(self, db_path):
        assert subscribe("not-an-email", path=db_path) is False

    def test_subscribe_empty_email(self, db_path):
        assert subscribe("", path=db_path) is False

    def test_subscribe_duplicate(self, db_path):
        subscribe("dup@example.com", path=db_path)
        assert subscribe("dup@example.com", path=db_path) is False

    def test_subscribe_with_user_id(self, db_path):
        assert subscribe("pro@example.com", user_id=42, path=db_path) is True

    def test_subscribe_multiple_emails(self, db_path):
        assert subscribe("a@example.com", path=db_path) is True
        assert subscribe("b@example.com", path=db_path) is True
        assert subscribe("c@example.com", path=db_path) is True

    def test_subscribe_email_formats(self, db_path):
        assert subscribe("user+tag@example.com", path=db_path) is True
        assert subscribe("first.last@example.com", path=db_path) is True

    def test_subscribe_rejects_bad_formats(self, db_path):
        assert subscribe("@example.com", path=db_path) is False
        assert subscribe("user@", path=db_path) is False
        assert subscribe("user@.com", path=db_path) is False


class TestUnsubscribe:
    def test_unsubscribe_existing(self, db_path):
        subscribe("bye@example.com", path=db_path)
        assert unsubscribe("bye@example.com", path=db_path) is True

    def test_unsubscribe_nonexistent(self, db_path):
        assert unsubscribe("ghost@example.com", path=db_path) is False

    def test_unsubscribe_removes_from_count(self, db_path):
        subscribe("temp@example.com", path=db_path)
        assert get_subscriber_count(db_path) == 1
        unsubscribe("temp@example.com", path=db_path)
        assert get_subscriber_count(db_path) == 0

    def test_double_unsubscribe(self, db_path):
        subscribe("once@example.com", path=db_path)
        assert unsubscribe("once@example.com", path=db_path) is True
        assert unsubscribe("once@example.com", path=db_path) is False


class TestGetSubscriberCount:
    def test_count_empty(self, db_path):
        assert get_subscriber_count(db_path) == 0

    def test_count_after_subscribes(self, db_path):
        for i in range(5):
            subscribe(f"user{i}@example.com", path=db_path)
        assert get_subscriber_count(db_path) == 5


class TestBuildWeeklyDigest:
    def test_digest_structure(self, seeded_db):
        digest = build_weekly_digest(seeded_db)
        assert "title" in digest
        assert "subscriber_count" in digest
        assert "trending" in digest
        assert "new_repos" in digest
        assert "sponsor" in digest

    def test_digest_title_format(self, seeded_db):
        digest = build_weekly_digest(seeded_db)
        assert "Reepo Weekly" in digest["title"]

    def test_digest_has_trending(self, seeded_db):
        digest = build_weekly_digest(seeded_db)
        assert len(digest["trending"]) > 0

    def test_digest_subscriber_count(self, seeded_db):
        subscribe("a@test.com", path=seeded_db)
        subscribe("b@test.com", path=seeded_db)
        digest = build_weekly_digest(seeded_db)
        assert digest["subscriber_count"] == 2

    def test_digest_no_sponsor(self, seeded_db):
        digest = build_weekly_digest(seeded_db)
        assert digest["sponsor"] is None

    def test_digest_empty_db(self, db_path):
        digest = build_weekly_digest(db_path)
        assert digest["trending"] == []
        assert digest["subscriber_count"] == 0


class TestGetLatestNewsletter:
    def test_latest_equals_digest(self, seeded_db):
        latest = get_latest_newsletter(seeded_db)
        digest = build_weekly_digest(seeded_db)
        assert latest["title"] == digest["title"]
        assert latest["subscriber_count"] == digest["subscriber_count"]
