"""Tests for the Reepo similar repos engine."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.seed import seed_database
from src.similar import find_similar, _jaccard_similarity, _star_proximity


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def seeded_db(db_path):
    seed_database(db_path)
    return db_path


# --- _jaccard_similarity ---

class TestJaccardSimilarity:
    def test_identical_sets(self):
        assert _jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0

    def test_disjoint_sets(self):
        assert _jaccard_similarity({"a"}, {"b"}) == 0.0

    def test_partial_overlap(self):
        result = _jaccard_similarity({"a", "b", "c"}, {"b", "c", "d"})
        assert abs(result - 0.5) < 0.01

    def test_empty_both(self):
        assert _jaccard_similarity(set(), set()) == 0.0

    def test_one_empty(self):
        assert _jaccard_similarity({"a"}, set()) == 0.0

    def test_subset(self):
        result = _jaccard_similarity({"a", "b"}, {"a", "b", "c"})
        assert abs(result - 2 / 3) < 0.01

    def test_single_overlap(self):
        result = _jaccard_similarity({"a", "b"}, {"a", "c"})
        assert abs(result - 1 / 3) < 0.01

    def test_large_sets(self):
        s1 = set(range(100))
        s2 = set(range(50, 150))
        result = _jaccard_similarity(s1, s2)
        assert abs(result - 50 / 150) < 0.01


# --- _star_proximity ---

class TestStarProximity:
    def test_identical_stars(self):
        assert _star_proximity(1000, 1000) == 1.0

    def test_similar_stars(self):
        result = _star_proximity(1000, 1200)
        assert result > 0.9

    def test_very_different(self):
        result = _star_proximity(10, 100000)
        assert result < 0.5

    def test_zero_stars(self):
        assert _star_proximity(0, 100) == 0.0

    def test_both_zero(self):
        assert _star_proximity(0, 0) == 0.0

    def test_one_star(self):
        result = _star_proximity(1, 1)
        assert result == 1.0

    def test_symmetry(self):
        assert _star_proximity(100, 1000) == _star_proximity(1000, 100)


# --- find_similar ---

class TestFindSimilar:
    def test_returns_list(self, seeded_db):
        result = find_similar(seeded_db, "langchain-ai", "langchain")
        assert isinstance(result, list)

    def test_not_empty_for_popular(self, seeded_db):
        result = find_similar(seeded_db, "langchain-ai", "langchain")
        assert len(result) > 0

    def test_excludes_self(self, seeded_db):
        result = find_similar(seeded_db, "langchain-ai", "langchain")
        for r in result:
            assert r["full_name"] != "langchain-ai/langchain"

    def test_same_category(self, seeded_db):
        from src.db import get_repo
        target = get_repo("langchain-ai", "langchain", seeded_db)
        result = find_similar(seeded_db, "langchain-ai", "langchain")
        for r in result:
            assert r["category_primary"] == target["category_primary"]

    def test_has_similarity_score(self, seeded_db):
        result = find_similar(seeded_db, "langchain-ai", "langchain")
        for r in result:
            assert "similarity_score" in r
            assert 0 < r["similarity_score"] <= 1

    def test_ordered_by_similarity(self, seeded_db):
        result = find_similar(seeded_db, "langchain-ai", "langchain")
        scores = [r["similarity_score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_respects_limit(self, seeded_db):
        result = find_similar(seeded_db, "langchain-ai", "langchain", limit=3)
        assert len(result) <= 3

    def test_nonexistent_repo(self, seeded_db):
        result = find_similar(seeded_db, "nonexistent", "repo")
        assert result == []

    def test_repo_with_no_matches(self, db_path):
        init_db(db_path)
        insert_repo({
            "github_id": 1, "owner": "solo", "name": "repo",
            "full_name": "solo/repo", "description": "unique",
            "stars": 10, "forks": 1, "language": "Rust",
            "topics": ["unique-topic"], "category_primary": "apps",
        }, db_path)
        result = find_similar(db_path, "solo", "repo")
        assert result == []

    def test_different_repos_similar(self, seeded_db):
        # pytorch and tensorflow should be similar (both frameworks)
        from src.db import get_repo
        target = get_repo("pytorch", "pytorch", seeded_db)
        if target:
            result = find_similar(seeded_db, "pytorch", "pytorch")
            names = [r["full_name"] for r in result]
            # Should find other ML frameworks
            assert len(result) > 0
