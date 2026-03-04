"""Tests for scheduler module — discover, reanalyze, velocity, daily job."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.growth.db import init_growth_db
from src.growth.scheduler import DailyCrawlScheduler


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_growth_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def seeded_db(db_path):
    for i in range(5):
        insert_repo({
            "github_id": i + 1, "owner": f"org{i}", "name": f"repo{i}",
            "full_name": f"org{i}/repo{i}", "description": f"Repo {i}",
            "stars": 1000 * (5 - i), "language": "Python",
            "topics": '["machine-learning", "ai"]',
            "category_primary": "frameworks",
        }, db_path)
    return db_path


class TestDiscoverNewRepos:
    def test_discover_with_matching_topics(self, seeded_db):
        scheduler = DailyCrawlScheduler(db_path=seeded_db)
        result = scheduler.discover_new_repos(["machine-learning", "ai"])
        assert result["topics_searched"] == 2

    def test_discover_with_no_matching_topics(self, seeded_db):
        scheduler = DailyCrawlScheduler(db_path=seeded_db)
        result = scheduler.discover_new_repos(["blockchain"])
        assert result["topics_searched"] == 1

    def test_discover_empty_db(self, db_path):
        scheduler = DailyCrawlScheduler(db_path=db_path)
        result = scheduler.discover_new_repos(["ai"])
        assert result["topics_searched"] == 1

    def test_discover_empty_topics(self, seeded_db):
        scheduler = DailyCrawlScheduler(db_path=seeded_db)
        result = scheduler.discover_new_repos([])
        assert result["topics_searched"] == 0


class TestReanalyzeStaleRepos:
    def test_all_repos_stale_no_analysis(self, seeded_db):
        scheduler = DailyCrawlScheduler(db_path=seeded_db)
        result = scheduler.reanalyze_stale_repos()
        assert result["stale_count"] == 5
        assert result["batch_size"] == 100

    def test_batch_size_limit(self, seeded_db):
        scheduler = DailyCrawlScheduler(db_path=seeded_db)
        result = scheduler.reanalyze_stale_repos(batch_size=2)
        assert result["stale_count"] == 2
        assert result["batch_size"] == 2

    def test_custom_max_age(self, seeded_db):
        scheduler = DailyCrawlScheduler(db_path=seeded_db)
        result = scheduler.reanalyze_stale_repos(max_age_days=30)
        assert result["stale_count"] >= 0

    def test_empty_db(self, db_path):
        scheduler = DailyCrawlScheduler(db_path=db_path)
        result = scheduler.reanalyze_stale_repos()
        assert result["stale_count"] == 0


class TestUpdateStarVelocity:
    def test_velocity_with_repos(self, seeded_db):
        scheduler = DailyCrawlScheduler(db_path=seeded_db)
        result = scheduler.update_star_velocity()
        assert result["repos_checked"] == 5

    def test_velocity_empty_db(self, db_path):
        scheduler = DailyCrawlScheduler(db_path=db_path)
        result = scheduler.update_star_velocity()
        assert result["repos_checked"] == 0


class TestRunDailyJob:
    def test_daily_job_returns_all_sections(self, seeded_db):
        scheduler = DailyCrawlScheduler(db_path=seeded_db)
        result = scheduler.run_daily_job()
        assert "ran_at" in result
        assert "discover" in result
        assert "reanalyze" in result
        assert "velocity" in result

    def test_daily_job_sets_last_run(self, seeded_db):
        scheduler = DailyCrawlScheduler(db_path=seeded_db)
        assert scheduler.last_run is None
        scheduler.run_daily_job()
        assert scheduler.last_run is not None

    def test_daily_job_empty_db(self, db_path):
        scheduler = DailyCrawlScheduler(db_path=db_path)
        result = scheduler.run_daily_job()
        assert "ran_at" in result
