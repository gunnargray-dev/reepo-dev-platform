"""Tests for the Reepo database layer."""
import json
import os
import tempfile

import pytest

from src.db import (
    init_db,
    insert_repo,
    update_repo,
    upsert_repo,
    get_repo,
    get_repo_by_id,
    list_repos,
    count_repos,
    get_unscored_repos,
    record_score,
    get_score_history,
    get_categories,
    get_repos_by_category,
    get_repos_by_language,
    get_score_stats,
    CATEGORIES,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    os.unlink(path)


def _make_repo(**overrides):
    base = {
        "github_id": 1001,
        "owner": "test-org",
        "name": "test-repo",
        "full_name": "test-org/test-repo",
        "description": "A test repository",
        "url": "https://github.com/test-org/test-repo",
        "stars": 500,
        "forks": 50,
        "language": "Python",
        "license": "MIT",
        "topics": ["ai", "test"],
        "category_primary": "libraries",
        "categories_secondary": ["tools-utilities"],
        "open_issues": 10,
        "has_wiki": True,
        "homepage": "https://test.dev",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2025-06-01T00:00:00Z",
        "pushed_at": "2025-06-01T00:00:00Z",
    }
    base.update(overrides)
    return base


# --- init_db ---

class TestInitDb:
    def test_creates_tables(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "repos" in table_names
        assert "score_history" in table_names
        assert "categories" in table_names
        conn.close()

    def test_seeds_categories(self, db_path):
        cats = get_categories(db_path)
        assert len(cats) == 10

    def test_category_slugs(self, db_path):
        cats = get_categories(db_path)
        slugs = {c["slug"] for c in cats}
        expected = {c[0] for c in CATEGORIES}
        assert slugs == expected

    def test_idempotent(self, db_path):
        init_db(db_path)
        init_db(db_path)
        cats = get_categories(db_path)
        assert len(cats) == 10

    def test_creates_indexes(self, db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        ).fetchall()
        idx_names = {i[0] for i in indexes}
        assert "idx_repos_stars" in idx_names
        assert "idx_repos_score" in idx_names
        assert "idx_repos_category" in idx_names
        assert "idx_repos_language" in idx_names
        assert "idx_repos_updated" in idx_names
        conn.close()

    def test_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "deep", "reepo.db")
            init_db(path)
            assert os.path.exists(path)
            os.unlink(path)


# --- insert_repo ---

class TestInsertRepo:
    def test_basic_insert(self, db_path):
        repo = _make_repo()
        repo_id = insert_repo(repo, db_path)
        assert repo_id >= 1

    def test_returns_id(self, db_path):
        repo_id = insert_repo(_make_repo(), db_path)
        assert isinstance(repo_id, int)

    def test_unique_github_id(self, db_path):
        insert_repo(_make_repo(), db_path)
        with pytest.raises(Exception):
            insert_repo(_make_repo(), db_path)

    def test_different_github_ids(self, db_path):
        id1 = insert_repo(_make_repo(github_id=1001), db_path)
        id2 = insert_repo(_make_repo(github_id=1002, name="test-repo-2", full_name="test-org/test-repo-2"), db_path)
        assert id1 != id2

    def test_stores_topics_as_json(self, db_path):
        insert_repo(_make_repo(topics=["ai", "ml", "python"]), db_path)
        repo = get_repo("test-org", "test-repo", db_path)
        assert repo["topics"] == ["ai", "ml", "python"]

    def test_stores_categories_secondary_as_json(self, db_path):
        insert_repo(_make_repo(categories_secondary=["agents", "frameworks"]), db_path)
        repo = get_repo("test-org", "test-repo", db_path)
        assert repo["categories_secondary"] == ["agents", "frameworks"]

    def test_null_optional_fields(self, db_path):
        repo = _make_repo(description=None, license=None, homepage=None)
        insert_repo(repo, db_path)
        fetched = get_repo("test-org", "test-repo", db_path)
        assert fetched["description"] is None

    def test_has_wiki_stored_as_int(self, db_path):
        insert_repo(_make_repo(has_wiki=True), db_path)
        import sqlite3
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT has_wiki FROM repos WHERE github_id = 1001").fetchone()
        assert row[0] == 1
        conn.close()

    def test_has_wiki_false(self, db_path):
        insert_repo(_make_repo(has_wiki=False), db_path)
        import sqlite3
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT has_wiki FROM repos WHERE github_id = 1001").fetchone()
        assert row[0] == 0
        conn.close()

    def test_indexed_at_set(self, db_path):
        insert_repo(_make_repo(), db_path)
        repo = get_repo("test-org", "test-repo", db_path)
        assert repo["indexed_at"] is not None


# --- update_repo ---

class TestUpdateRepo:
    def test_update_existing(self, db_path):
        insert_repo(_make_repo(stars=100), db_path)
        updated = update_repo(_make_repo(stars=200), db_path)
        assert updated is True
        repo = get_repo("test-org", "test-repo", db_path)
        assert repo["stars"] == 200

    def test_update_nonexistent(self, db_path):
        updated = update_repo(_make_repo(github_id=9999), db_path)
        assert updated is False

    def test_update_description(self, db_path):
        insert_repo(_make_repo(), db_path)
        updated = update_repo(_make_repo(description="Updated description"), db_path)
        assert updated is True
        repo = get_repo("test-org", "test-repo", db_path)
        assert repo["description"] == "Updated description"

    def test_update_topics(self, db_path):
        insert_repo(_make_repo(topics=["old"]), db_path)
        update_repo(_make_repo(topics=["new", "updated"]), db_path)
        repo = get_repo("test-org", "test-repo", db_path)
        assert repo["topics"] == ["new", "updated"]

    def test_update_category(self, db_path):
        insert_repo(_make_repo(category_primary="libraries"), db_path)
        update_repo(_make_repo(category_primary="frameworks"), db_path)
        repo = get_repo("test-org", "test-repo", db_path)
        assert repo["category_primary"] == "frameworks"


# --- upsert_repo ---

class TestUpsertRepo:
    def test_upsert_insert(self, db_path):
        repo_id = upsert_repo(_make_repo(), db_path)
        assert repo_id >= 1
        assert count_repos(db_path) == 1

    def test_upsert_update(self, db_path):
        upsert_repo(_make_repo(stars=100), db_path)
        upsert_repo(_make_repo(stars=200), db_path)
        assert count_repos(db_path) == 1
        repo = get_repo("test-org", "test-repo", db_path)
        assert repo["stars"] == 200

    def test_upsert_returns_existing_id(self, db_path):
        id1 = upsert_repo(_make_repo(), db_path)
        id2 = upsert_repo(_make_repo(stars=999), db_path)
        assert id1 == id2


# --- get_repo ---

class TestGetRepo:
    def test_existing(self, db_path):
        insert_repo(_make_repo(), db_path)
        repo = get_repo("test-org", "test-repo", db_path)
        assert repo is not None
        assert repo["full_name"] == "test-org/test-repo"

    def test_nonexistent(self, db_path):
        repo = get_repo("nope", "nope", db_path)
        assert repo is None

    def test_returns_all_fields(self, db_path):
        insert_repo(_make_repo(), db_path)
        repo = get_repo("test-org", "test-repo", db_path)
        assert "id" in repo
        assert "github_id" in repo
        assert "owner" in repo
        assert "stars" in repo
        assert "topics" in repo
        assert "indexed_at" in repo


# --- get_repo_by_id ---

class TestGetRepoById:
    def test_existing(self, db_path):
        repo_id = insert_repo(_make_repo(), db_path)
        repo = get_repo_by_id(repo_id, db_path)
        assert repo is not None
        assert repo["id"] == repo_id

    def test_nonexistent(self, db_path):
        repo = get_repo_by_id(99999, db_path)
        assert repo is None


# --- list_repos ---

class TestListRepos:
    def test_empty(self, db_path):
        repos = list_repos(db_path)
        assert repos == []

    def test_returns_all(self, db_path):
        for i in range(5):
            insert_repo(_make_repo(github_id=2000 + i, name=f"repo-{i}", full_name=f"org/repo-{i}"), db_path)
        repos = list_repos(db_path)
        assert len(repos) == 5

    def test_filter_category(self, db_path):
        insert_repo(_make_repo(github_id=3001, name="a", full_name="o/a", category_primary="agents"), db_path)
        insert_repo(_make_repo(github_id=3002, name="b", full_name="o/b", category_primary="frameworks"), db_path)
        repos = list_repos(db_path, category="agents")
        assert len(repos) == 1
        assert repos[0]["category_primary"] == "agents"

    def test_filter_language(self, db_path):
        insert_repo(_make_repo(github_id=4001, name="a", full_name="o/a", language="Python"), db_path)
        insert_repo(_make_repo(github_id=4002, name="b", full_name="o/b", language="Rust"), db_path)
        repos = list_repos(db_path, language="Rust")
        assert len(repos) == 1
        assert repos[0]["language"] == "Rust"

    def test_filter_min_score(self, db_path):
        id1 = insert_repo(_make_repo(github_id=5001, name="a", full_name="o/a"), db_path)
        id2 = insert_repo(_make_repo(github_id=5002, name="b", full_name="o/b"), db_path)
        record_score(id1, 90, {"test": 90}, db_path)
        record_score(id2, 30, {"test": 30}, db_path)
        repos = list_repos(db_path, min_score=50)
        assert len(repos) == 1
        assert repos[0]["reepo_score"] == 90

    def test_sort_by_stars(self, db_path):
        insert_repo(_make_repo(github_id=6001, name="a", full_name="o/a", stars=10), db_path)
        insert_repo(_make_repo(github_id=6002, name="b", full_name="o/b", stars=1000), db_path)
        repos = list_repos(db_path, sort_by="stars")
        assert repos[0]["stars"] >= repos[1]["stars"]

    def test_sort_by_name(self, db_path):
        insert_repo(_make_repo(github_id=7001, name="zebra", full_name="o/zebra"), db_path)
        insert_repo(_make_repo(github_id=7002, name="alpha", full_name="o/alpha"), db_path)
        repos = list_repos(db_path, sort_by="name")
        assert repos[0]["name"] == "alpha"

    def test_limit(self, db_path):
        for i in range(10):
            insert_repo(_make_repo(github_id=8000 + i, name=f"r{i}", full_name=f"o/r{i}"), db_path)
        repos = list_repos(db_path, limit=3)
        assert len(repos) == 3

    def test_offset(self, db_path):
        for i in range(5):
            insert_repo(_make_repo(github_id=9000 + i, name=f"r{i}", full_name=f"o/r{i}", stars=100 - i * 10), db_path)
        all_repos = list_repos(db_path)
        offset_repos = list_repos(db_path, offset=2)
        assert len(offset_repos) == 3
        assert offset_repos[0]["github_id"] == all_repos[2]["github_id"]

    def test_invalid_sort_defaults_to_stars(self, db_path):
        insert_repo(_make_repo(github_id=10001, name="a", full_name="o/a", stars=50), db_path)
        repos = list_repos(db_path, sort_by="invalid_column; DROP TABLE repos")
        assert len(repos) == 1

    def test_combined_filters(self, db_path):
        insert_repo(_make_repo(github_id=11001, name="a", full_name="o/a", language="Python", category_primary="agents"), db_path)
        insert_repo(_make_repo(github_id=11002, name="b", full_name="o/b", language="Rust", category_primary="agents"), db_path)
        insert_repo(_make_repo(github_id=11003, name="c", full_name="o/c", language="Python", category_primary="frameworks"), db_path)
        repos = list_repos(db_path, category="agents", language="Python")
        assert len(repos) == 1
        assert repos[0]["name"] == "a"


# --- count_repos ---

class TestCountRepos:
    def test_empty(self, db_path):
        assert count_repos(db_path) == 0

    def test_with_repos(self, db_path):
        for i in range(3):
            insert_repo(_make_repo(github_id=12000 + i, name=f"r{i}", full_name=f"o/r{i}"), db_path)
        assert count_repos(db_path) == 3


# --- get_unscored_repos ---

class TestGetUnscoredRepos:
    def test_all_unscored(self, db_path):
        insert_repo(_make_repo(), db_path)
        unscored = get_unscored_repos(db_path)
        assert len(unscored) == 1

    def test_none_unscored(self, db_path):
        repo_id = insert_repo(_make_repo(), db_path)
        record_score(repo_id, 80, {"test": 80}, db_path)
        unscored = get_unscored_repos(db_path)
        assert len(unscored) == 0

    def test_mixed(self, db_path):
        id1 = insert_repo(_make_repo(github_id=13001, name="a", full_name="o/a"), db_path)
        insert_repo(_make_repo(github_id=13002, name="b", full_name="o/b"), db_path)
        record_score(id1, 80, {"test": 80}, db_path)
        unscored = get_unscored_repos(db_path)
        assert len(unscored) == 1
        assert unscored[0]["name"] == "b"


# --- record_score / get_score_history ---

class TestScoreHistory:
    def test_record_and_get(self, db_path):
        repo_id = insert_repo(_make_repo(), db_path)
        record_score(repo_id, 85, {"maintenance_health": 90, "popularity": 80}, db_path)
        history = get_score_history(repo_id, db_path)
        assert len(history) == 1
        assert history[0]["reepo_score"] == 85

    def test_multiple_records(self, db_path):
        repo_id = insert_repo(_make_repo(), db_path)
        record_score(repo_id, 80, {"a": 80}, db_path)
        record_score(repo_id, 85, {"a": 85}, db_path)
        record_score(repo_id, 90, {"a": 90}, db_path)
        history = get_score_history(repo_id, db_path)
        assert len(history) == 3
        scores = {h["reepo_score"] for h in history}
        assert scores == {80, 85, 90}

    def test_updates_repo_score(self, db_path):
        repo_id = insert_repo(_make_repo(), db_path)
        record_score(repo_id, 75, {"a": 75}, db_path)
        repo = get_repo_by_id(repo_id, db_path)
        assert repo["reepo_score"] == 75

    def test_updates_last_analyzed(self, db_path):
        repo_id = insert_repo(_make_repo(), db_path)
        record_score(repo_id, 75, {"a": 75}, db_path)
        repo = get_repo_by_id(repo_id, db_path)
        assert repo["last_analyzed_at"] is not None

    def test_score_breakdown_json(self, db_path):
        repo_id = insert_repo(_make_repo(), db_path)
        breakdown = {"maintenance_health": 90, "popularity": 70}
        record_score(repo_id, 80, breakdown, db_path)
        history = get_score_history(repo_id, db_path)
        parsed = json.loads(history[0]["score_breakdown"])
        assert parsed["maintenance_health"] == 90

    def test_empty_history(self, db_path):
        repo_id = insert_repo(_make_repo(), db_path)
        history = get_score_history(repo_id, db_path)
        assert history == []


# --- get_categories ---

class TestGetCategories:
    def test_returns_all(self, db_path):
        cats = get_categories(db_path)
        assert len(cats) == 10

    def test_category_fields(self, db_path):
        cats = get_categories(db_path)
        for cat in cats:
            assert "slug" in cat
            assert "name" in cat
            assert "description" in cat
            assert "repo_count" in cat

    def test_sorted_by_name(self, db_path):
        cats = get_categories(db_path)
        names = [c["name"] for c in cats]
        assert names == sorted(names)

    def test_initial_repo_count_zero(self, db_path):
        cats = get_categories(db_path)
        for cat in cats:
            assert cat["repo_count"] == 0


# --- get_repos_by_category ---

class TestGetReposByCategory:
    def test_empty(self, db_path):
        result = get_repos_by_category(db_path)
        assert result == {}

    def test_counts(self, db_path):
        insert_repo(_make_repo(github_id=14001, name="a", full_name="o/a", category_primary="agents"), db_path)
        insert_repo(_make_repo(github_id=14002, name="b", full_name="o/b", category_primary="agents"), db_path)
        insert_repo(_make_repo(github_id=14003, name="c", full_name="o/c", category_primary="frameworks"), db_path)
        result = get_repos_by_category(db_path)
        assert result["agents"] == 2
        assert result["frameworks"] == 1


# --- get_repos_by_language ---

class TestGetReposByLanguage:
    def test_empty(self, db_path):
        result = get_repos_by_language(db_path)
        assert result == {}

    def test_counts(self, db_path):
        insert_repo(_make_repo(github_id=15001, name="a", full_name="o/a", language="Python"), db_path)
        insert_repo(_make_repo(github_id=15002, name="b", full_name="o/b", language="Python"), db_path)
        insert_repo(_make_repo(github_id=15003, name="c", full_name="o/c", language="Rust"), db_path)
        result = get_repos_by_language(db_path)
        assert result["Python"] == 2
        assert result["Rust"] == 1

    def test_limit(self, db_path):
        for i, lang in enumerate(["Python", "Rust", "Go", "Java", "TypeScript"]):
            insert_repo(_make_repo(github_id=16000 + i, name=f"r{i}", full_name=f"o/r{i}", language=lang), db_path)
        result = get_repos_by_language(db_path, limit=3)
        assert len(result) == 3

    def test_excludes_null_language(self, db_path):
        insert_repo(_make_repo(github_id=17001, name="a", full_name="o/a", language=None), db_path)
        insert_repo(_make_repo(github_id=17002, name="b", full_name="o/b", language="Python"), db_path)
        result = get_repos_by_language(db_path)
        assert None not in result
        assert len(result) == 1


# --- get_score_stats ---

class TestGetScoreStats:
    def test_empty(self, db_path):
        stats = get_score_stats(db_path)
        assert stats["avg_score"] == 0

    def test_with_scores(self, db_path):
        id1 = insert_repo(_make_repo(github_id=18001, name="a", full_name="o/a"), db_path)
        id2 = insert_repo(_make_repo(github_id=18002, name="b", full_name="o/b"), db_path)
        record_score(id1, 80, {}, db_path)
        record_score(id2, 60, {}, db_path)
        stats = get_score_stats(db_path)
        assert stats["avg_score"] == 70
        assert stats["min_score"] == 60
        assert stats["max_score"] == 80

    def test_distribution(self, db_path):
        scores = [90, 85, 70, 65, 50, 45, 30, 20]
        for i, score in enumerate(scores):
            repo_id = insert_repo(_make_repo(github_id=19000 + i, name=f"r{i}", full_name=f"o/r{i}"), db_path)
            record_score(repo_id, score, {}, db_path)
        stats = get_score_stats(db_path)
        dist = stats["distribution"]
        assert dist["excellent_80_plus"] == 2
        assert dist["good_60_79"] == 2
        assert dist["fair_40_59"] == 2
        assert dist["poor_below_40"] == 2
