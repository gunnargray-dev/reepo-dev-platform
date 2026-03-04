"""Tests for the Reepo seed data module."""
import os
import tempfile

import pytest

from src.seed import SEED_REPOS, generate_seed_repos, seed_database, _add_timestamps
from src.db import (
    init_db,
    count_repos,
    get_repo,
    get_repo_by_id,
    get_categories,
    get_repos_by_category,
    get_score_stats,
)


# --- SEED_REPOS ---

class TestSeedReposData:
    def test_has_50_repos(self):
        assert len(SEED_REPOS) == 50

    def test_all_have_github_id(self):
        for repo in SEED_REPOS:
            assert "github_id" in repo

    def test_unique_github_ids(self):
        ids = [r["github_id"] for r in SEED_REPOS]
        assert len(ids) == len(set(ids))

    def test_all_have_owner(self):
        for repo in SEED_REPOS:
            assert "owner" in repo and repo["owner"]

    def test_all_have_name(self):
        for repo in SEED_REPOS:
            assert "name" in repo and repo["name"]

    def test_all_have_full_name(self):
        for repo in SEED_REPOS:
            assert "full_name" in repo

    def test_all_have_description(self):
        for repo in SEED_REPOS:
            assert "description" in repo

    def test_all_have_stars(self):
        for repo in SEED_REPOS:
            assert "stars" in repo
            assert isinstance(repo["stars"], int)

    def test_all_have_topics(self):
        for repo in SEED_REPOS:
            assert "topics" in repo
            assert isinstance(repo["topics"], list)

    def test_star_range(self):
        stars = [r["stars"] for r in SEED_REPOS]
        assert max(stars) > 100000  # Has mega-popular repos
        assert min(stars) < 20  # Has small repos

    def test_language_diversity(self):
        langs = {r.get("language") for r in SEED_REPOS}
        assert len(langs) >= 4

    def test_has_known_repos(self):
        names = {r["name"] for r in SEED_REPOS}
        assert "langchain" in names
        assert "transformers" in names
        assert "pytorch" in names

    def test_license_variety(self):
        licenses = {r.get("license") for r in SEED_REPOS}
        assert "MIT" in licenses
        assert "Apache-2.0" in licenses

    def test_has_readme_excerpts(self):
        with_readme = [r for r in SEED_REPOS if r.get("readme_excerpt")]
        assert len(with_readme) >= 40


# --- _add_timestamps ---

class TestAddTimestamps:
    def test_adds_created_at(self):
        repo = {"name": "test"}
        result = _add_timestamps(repo, 365, True)
        assert "created_at" in result

    def test_adds_updated_at(self):
        repo = {"name": "test"}
        result = _add_timestamps(repo, 365, True)
        assert "updated_at" in result

    def test_adds_pushed_at(self):
        repo = {"name": "test"}
        result = _add_timestamps(repo, 365, True)
        assert "pushed_at" in result

    def test_active_push_recent(self):
        repo = {"name": "test"}
        result = _add_timestamps(repo, 365, active=True)
        from datetime import datetime, timezone
        pushed = datetime.fromisoformat(result["pushed_at"])
        now = datetime.now(timezone.utc)
        delta = (now - pushed).days
        assert delta < 30

    def test_inactive_push_old(self):
        repo = {"name": "test"}
        result = _add_timestamps(repo, 365, active=False)
        from datetime import datetime, timezone
        pushed = datetime.fromisoformat(result["pushed_at"])
        now = datetime.now(timezone.utc)
        delta = (now - pushed).days
        assert delta >= 180


# --- generate_seed_repos ---

class TestGenerateSeedRepos:
    def test_returns_50(self):
        repos = generate_seed_repos()
        assert len(repos) == 50

    def test_all_have_timestamps(self):
        repos = generate_seed_repos()
        for repo in repos:
            assert "created_at" in repo
            assert "updated_at" in repo
            assert "pushed_at" in repo

    def test_all_classified(self):
        repos = generate_seed_repos()
        for repo in repos:
            assert "category_primary" in repo
            assert "categories_secondary" in repo

    def test_categories_are_valid(self):
        from src.taxonomy import CATEGORIES as TAX_CATS
        valid = set(TAX_CATS.keys())
        repos = generate_seed_repos()
        for repo in repos:
            assert repo["category_primary"] in valid

    def test_returns_new_copies(self):
        repos1 = generate_seed_repos()
        repos2 = generate_seed_repos()
        repos1[0]["name"] = "modified"
        assert repos2[0]["name"] != "modified"


# --- seed_database ---

class TestSeedDatabase:
    @pytest.fixture
    def db_path(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)

    def test_returns_50(self, db_path):
        count = seed_database(db_path)
        assert count == 50

    def test_populates_db(self, db_path):
        seed_database(db_path)
        assert count_repos(db_path) == 50

    def test_repos_have_scores(self, db_path):
        seed_database(db_path)
        repo = get_repo_by_id(1, db_path)
        assert repo["reepo_score"] is not None
        assert repo["reepo_score"] > 0

    def test_categories_populated(self, db_path):
        seed_database(db_path)
        by_cat = get_repos_by_category(db_path)
        assert len(by_cat) > 0

    def test_score_stats(self, db_path):
        seed_database(db_path)
        stats = get_score_stats(db_path)
        assert stats["avg_score"] > 0

    def test_known_repo_stored(self, db_path):
        seed_database(db_path)
        repo = get_repo("langchain-ai", "langchain", db_path)
        assert repo is not None
        assert repo["stars"] == 95000

    def test_idempotent(self, db_path):
        seed_database(db_path)
        seed_database(db_path)
        assert count_repos(db_path) == 50

    def test_all_have_score_breakdown(self, db_path):
        seed_database(db_path)
        from src.db import list_repos
        repos = list_repos(db_path, limit=50)
        for repo in repos:
            assert repo["score_breakdown"] is not None

    def test_score_range(self, db_path):
        seed_database(db_path)
        stats = get_score_stats(db_path)
        assert stats["min_score"] > 0
        assert stats["max_score"] <= 100
        dist = stats["distribution"]
        total = sum(dist.values())
        assert total == 50
