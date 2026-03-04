"""Tests for sponsored listings — CRUD, impressions, clicks, analytics."""
import os
import tempfile
from datetime import date, timedelta

import pytest

from src.db import init_db, insert_repo
from src.monetization.db import init_monetization_db
from src.monetization.sponsors import (
    create_sponsor,
    create_listing,
    get_active_sponsored_for_category,
    record_impression,
    record_click,
    get_sponsor_analytics,
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
def sample_repo(db_path):
    repo_id = insert_repo({
        "github_id": 200001,
        "owner": "test-org",
        "name": "test-repo",
        "full_name": "test-org/test-repo",
        "description": "A test repo",
        "stars": 5000,
        "category_primary": "frameworks",
        "language": "Python",
    }, db_path)
    return repo_id


@pytest.fixture
def sponsor(db_path):
    return create_sponsor("TestCorp", "https://logo.png", "https://testcorp.com", "hi@test.com", db_path)


@pytest.fixture
def active_listing(db_path, sponsor, sample_repo):
    today = date.today()
    return create_listing(
        sponsor, sample_repo,
        "https://testcorp.com/promo",
        (today - timedelta(days=1)).isoformat(),
        (today + timedelta(days=30)).isoformat(),
        db_path,
    )


class TestCreateSponsor:
    def test_create_sponsor(self, db_path):
        sid = create_sponsor("Acme", path=db_path)
        assert sid > 0

    def test_create_sponsor_with_details(self, db_path):
        sid = create_sponsor("Acme", "https://logo.png", "https://acme.com", "hi@acme.com", db_path)
        assert sid > 0

    def test_multiple_sponsors(self, db_path):
        s1 = create_sponsor("A", path=db_path)
        s2 = create_sponsor("B", path=db_path)
        assert s1 != s2


class TestCreateListing:
    def test_create_listing(self, db_path, sponsor, sample_repo):
        lid = create_listing(sponsor, sample_repo, "https://url.com", "2026-01-01", "2026-12-31", db_path)
        assert lid > 0

    def test_multiple_listings(self, db_path, sponsor, sample_repo):
        l1 = create_listing(sponsor, sample_repo, "https://a.com", "2026-01-01", "2026-06-30", db_path)
        l2 = create_listing(sponsor, sample_repo, "https://b.com", "2026-07-01", "2026-12-31", db_path)
        assert l1 != l2


class TestActiveListing:
    def test_get_active_global(self, db_path, active_listing):
        result = get_active_sponsored_for_category(path=db_path)
        assert result is not None
        assert result["id"] == active_listing

    def test_get_active_for_category(self, db_path, active_listing):
        result = get_active_sponsored_for_category(category="frameworks", path=db_path)
        assert result is not None

    def test_no_active_wrong_category(self, db_path, active_listing):
        result = get_active_sponsored_for_category(category="datasets", path=db_path)
        assert result is None

    def test_no_active_when_expired(self, db_path, sponsor, sample_repo):
        create_listing(sponsor, sample_repo, "https://url.com", "2020-01-01", "2020-12-31", db_path)
        result = get_active_sponsored_for_category(path=db_path)
        # Only the expired listing exists
        assert result is None or result["end_date"] >= date.today().isoformat()

    def test_no_active_empty(self, db_path):
        result = get_active_sponsored_for_category(path=db_path)
        assert result is None


class TestImpressions:
    def test_record_impression(self, db_path, active_listing):
        record_impression(active_listing, db_path)
        listing = get_active_sponsored_for_category(path=db_path)
        assert listing["impressions"] == 1

    def test_multiple_impressions(self, db_path, active_listing):
        for _ in range(5):
            record_impression(active_listing, db_path)
        listing = get_active_sponsored_for_category(path=db_path)
        assert listing["impressions"] == 5


class TestClicks:
    def test_record_click(self, db_path, active_listing):
        record_click(active_listing, db_path)
        analytics = get_sponsor_analytics(1, db_path)
        total_clicks = analytics["totals"]["clicks"]
        assert total_clicks == 1

    def test_multiple_clicks(self, db_path, active_listing):
        for _ in range(3):
            record_click(active_listing, db_path)
        analytics = get_sponsor_analytics(1, db_path)
        assert analytics["totals"]["clicks"] == 3


class TestAnalytics:
    def test_analytics_structure(self, db_path, sponsor, active_listing):
        analytics = get_sponsor_analytics(sponsor, db_path)
        assert "sponsor" in analytics
        assert "listings" in analytics
        assert "totals" in analytics

    def test_analytics_ctr(self, db_path, sponsor, active_listing):
        for _ in range(100):
            record_impression(active_listing, db_path)
        for _ in range(5):
            record_click(active_listing, db_path)
        analytics = get_sponsor_analytics(sponsor, db_path)
        assert analytics["totals"]["ctr"] == 5.0

    def test_analytics_not_found(self, db_path):
        analytics = get_sponsor_analytics(999, db_path)
        assert "error" in analytics

    def test_analytics_listing_count(self, db_path, sponsor, sample_repo):
        today = date.today()
        for i in range(3):
            create_listing(sponsor, sample_repo, f"https://url{i}.com",
                         (today - timedelta(days=1)).isoformat(),
                         (today + timedelta(days=30)).isoformat(), db_path)
        analytics = get_sponsor_analytics(sponsor, db_path)
        assert len(analytics["listings"]) == 3
