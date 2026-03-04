"""Tests for the Reepo affiliate link system — seeding, lookup, clicks."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.monetization.db import init_monetization_db
from src.monetization.affiliates import (
    KNOWN_AFFILIATES,
    seed_affiliate_links,
    get_affiliate_link,
    get_affiliate_link_by_repo,
    record_affiliate_click,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_monetization_db(path)
    yield path
    os.unlink(path)


def _insert_known_repo(db_path, owner="supabase", name="supabase"):
    return insert_repo({
        "github_id": 90000,
        "owner": owner,
        "name": name,
        "full_name": f"{owner}/{name}",
        "description": "Test affiliate repo",
        "stars": 1000,
        "language": "TypeScript",
    }, db_path)


class TestKnownAffiliates:
    def test_known_affiliates_not_empty(self):
        assert len(KNOWN_AFFILIATES) > 0

    def test_known_affiliates_has_supabase(self):
        names = [a["owner"] for a in KNOWN_AFFILIATES]
        assert "supabase" in names

    def test_known_affiliates_structure(self):
        for aff in KNOWN_AFFILIATES:
            assert "owner" in aff
            assert "name" in aff
            assert "provider" in aff
            assert "url" in aff


class TestSeedAffiliateLinks:
    def test_seed_no_matching_repos(self, db_path):
        count = seed_affiliate_links(db_path)
        assert count == 0

    def test_seed_with_matching_repo(self, db_path):
        _insert_known_repo(db_path)
        count = seed_affiliate_links(db_path)
        assert count == 1

    def test_seed_idempotent(self, db_path):
        _insert_known_repo(db_path)
        count1 = seed_affiliate_links(db_path)
        count2 = seed_affiliate_links(db_path)
        assert count1 == 1
        assert count2 == 0

    def test_seed_multiple_matches(self, db_path):
        _insert_known_repo(db_path, "supabase", "supabase")
        insert_repo({
            "github_id": 90001,
            "owner": "vercel",
            "name": "next.js",
            "full_name": "vercel/next.js",
            "description": "React framework",
            "stars": 100000,
            "language": "JavaScript",
        }, db_path)
        count = seed_affiliate_links(db_path)
        assert count == 2


class TestGetAffiliateLink:
    def test_get_no_link(self, db_path):
        repo_id = insert_repo({
            "github_id": 91000,
            "owner": "no-aff",
            "name": "no-aff-repo",
            "full_name": "no-aff/no-aff-repo",
            "description": "No affiliate",
            "stars": 10,
            "language": "Python",
        }, db_path)
        assert get_affiliate_link(repo_id, db_path) is None

    def test_get_existing_link(self, db_path):
        repo_id = _insert_known_repo(db_path)
        seed_affiliate_links(db_path)
        link = get_affiliate_link(repo_id, db_path)
        assert link is not None
        assert link["provider"] == "Supabase"
        assert "supabase.com" in link["url"]

    def test_get_link_returns_dict(self, db_path):
        repo_id = _insert_known_repo(db_path)
        seed_affiliate_links(db_path)
        link = get_affiliate_link(repo_id, db_path)
        assert isinstance(link, dict)
        assert "id" in link
        assert "repo_id" in link


class TestGetAffiliateLinkByRepo:
    def test_get_by_repo_not_found(self, db_path):
        assert get_affiliate_link_by_repo("no", "repo", db_path) is None

    def test_get_by_repo_found(self, db_path):
        _insert_known_repo(db_path)
        seed_affiliate_links(db_path)
        link = get_affiliate_link_by_repo("supabase", "supabase", db_path)
        assert link is not None
        assert link["provider"] == "Supabase"

    def test_get_by_repo_wrong_name(self, db_path):
        _insert_known_repo(db_path)
        seed_affiliate_links(db_path)
        assert get_affiliate_link_by_repo("supabase", "wrong", db_path) is None


class TestRecordAffiliateClick:
    def test_record_click(self, db_path):
        repo_id = _insert_known_repo(db_path)
        seed_affiliate_links(db_path)
        link = get_affiliate_link(repo_id, db_path)
        initial_clicks = link.get("click_count", 0)
        record_affiliate_click(link["id"], db_path)
        updated = get_affiliate_link(repo_id, db_path)
        assert updated["click_count"] == initial_clicks + 1

    def test_multiple_clicks(self, db_path):
        repo_id = _insert_known_repo(db_path)
        seed_affiliate_links(db_path)
        link = get_affiliate_link(repo_id, db_path)
        for _ in range(5):
            record_affiliate_click(link["id"], db_path)
        updated = get_affiliate_link(repo_id, db_path)
        assert updated["click_count"] == 5

    def test_click_nonexistent_link(self, db_path):
        record_affiliate_click(99999, db_path)
