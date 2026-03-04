"""Tests for the Reepo full-text search module."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.search import init_fts, rebuild_fts, search, _sanitize_fts_query


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def seeded_db(db_path):
    repos = [
        {"github_id": 1, "owner": "org1", "name": "langchain", "full_name": "org1/langchain",
         "description": "Build LLM applications with composable chains", "stars": 90000,
         "topics": ["llm", "ai", "python"], "language": "Python", "category_primary": "frameworks",
         "readme_excerpt": "LangChain is a framework for developing applications powered by language models."},
        {"github_id": 2, "owner": "org2", "name": "pytorch", "full_name": "org2/pytorch",
         "description": "Tensors and dynamic neural networks in Python", "stars": 80000,
         "topics": ["deep-learning", "machine-learning", "python"], "language": "Python", "category_primary": "frameworks",
         "readme_excerpt": "PyTorch is an optimized tensor library for deep learning using GPUs and CPUs."},
        {"github_id": 3, "owner": "org3", "name": "ollama", "full_name": "org3/ollama",
         "description": "Get up and running with large language models locally", "stars": 50000,
         "topics": ["llm", "local", "inference"], "language": "Go", "category_primary": "apps",
         "readme_excerpt": "Run Llama 2, Mistral, and other models."},
        {"github_id": 4, "owner": "org4", "name": "vscode-ai", "full_name": "org4/vscode-ai",
         "description": "AI assistant extension for VS Code", "stars": 5000,
         "topics": ["vscode", "ai", "extension"], "language": "TypeScript", "category_primary": "tools-utilities",
         "readme_excerpt": "An AI-powered coding assistant for Visual Studio Code."},
        {"github_id": 5, "owner": "org5", "name": "ml-datasets", "full_name": "org5/ml-datasets",
         "description": "Curated collection of machine learning datasets", "stars": 3000,
         "topics": ["datasets", "machine-learning"], "language": "Python", "category_primary": "datasets",
         "readme_excerpt": "A comprehensive collection of ML datasets."},
    ]
    for repo in repos:
        insert_repo(repo, db_path)
    init_fts(db_path)
    return db_path


# --- init_fts / rebuild_fts ---

class TestInitFts:
    def test_creates_fts_table(self, db_path):
        init_fts(db_path)
        import sqlite3
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repos_fts'").fetchone()
        conn.close()
        assert row is not None

    def test_idempotent(self, db_path):
        init_fts(db_path)
        init_fts(db_path)

    def test_rebuild_fts(self, db_path):
        init_fts(db_path)
        rebuild_fts(db_path)
        import sqlite3
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repos_fts'").fetchone()
        conn.close()
        assert row is not None


# --- _sanitize_fts_query ---

class TestSanitizeFtsQuery:
    def test_simple_word(self):
        result = _sanitize_fts_query("langchain")
        assert '"langchain"' in result

    def test_multiple_words(self):
        result = _sanitize_fts_query("machine learning")
        assert '"machine"' in result
        assert '"learning"' in result
        assert "OR" in result

    def test_strips_special_chars(self):
        result = _sanitize_fts_query("test()")
        assert "(" not in result
        assert ")" not in result

    def test_empty_string(self):
        result = _sanitize_fts_query("")
        assert result == '""'

    def test_whitespace_only(self):
        result = _sanitize_fts_query("   ")
        assert result == '""'

    def test_special_chars_only(self):
        result = _sanitize_fts_query("()*[]")
        assert result == '""'

    def test_mixed_special_and_normal(self):
        result = _sanitize_fts_query("hello* world()")
        assert '"hello"' in result
        assert '"world"' in result


# --- search function ---

class TestSearch:
    def test_empty_query_returns_all(self, seeded_db):
        result = search(seeded_db, query="")
        assert result["total"] == 5

    def test_returns_pagination_fields(self, seeded_db):
        result = search(seeded_db, query="")
        assert "results" in result
        assert "total" in result
        assert "page" in result
        assert "per_page" in result
        assert "pages" in result

    def test_search_by_name(self, seeded_db):
        result = search(seeded_db, query="langchain")
        assert result["total"] >= 1
        names = [r["name"] for r in result["results"]]
        assert "langchain" in names

    def test_search_by_description(self, seeded_db):
        result = search(seeded_db, query="neural networks")
        assert result["total"] >= 1

    def test_filter_by_category(self, seeded_db):
        result = search(seeded_db, query="", category="frameworks")
        assert result["total"] == 2
        for r in result["results"]:
            assert r["category_primary"] == "frameworks"

    def test_filter_by_language(self, seeded_db):
        result = search(seeded_db, query="", language="Python")
        assert result["total"] == 3

    def test_filter_by_min_score(self, seeded_db):
        result = search(seeded_db, query="", min_score=999)
        assert result["total"] == 0

    def test_combined_filters(self, seeded_db):
        result = search(seeded_db, query="", category="frameworks", language="Python")
        assert result["total"] == 2

    def test_sort_by_stars(self, seeded_db):
        result = search(seeded_db, query="", sort="stars")
        stars = [r["stars"] for r in result["results"]]
        assert stars == sorted(stars, reverse=True)

    def test_pagination_page_1(self, seeded_db):
        result = search(seeded_db, query="", per_page=2, page=1)
        assert len(result["results"]) == 2
        assert result["page"] == 1

    def test_pagination_page_2(self, seeded_db):
        result = search(seeded_db, query="", per_page=2, page=2)
        assert len(result["results"]) == 2
        assert result["page"] == 2

    def test_pages_calculation(self, seeded_db):
        result = search(seeded_db, query="", per_page=2)
        assert result["pages"] == 3

    def test_no_results(self, seeded_db):
        result = search(seeded_db, query="xyznonexistent999")
        assert result["total"] == 0
        assert result["results"] == []

    def test_sort_by_score(self, seeded_db):
        result = search(seeded_db, query="", sort="score")
        assert len(result["results"]) == 5

    def test_sort_fallback_unknown(self, seeded_db):
        result = search(seeded_db, query="", sort="unknown")
        assert len(result["results"]) == 5

    def test_empty_db_search(self, db_path):
        init_fts(db_path)
        result = search(db_path, query="anything")
        assert result["total"] == 0

    def test_min_pages_is_one(self, db_path):
        init_fts(db_path)
        result = search(db_path, query="anything")
        assert result["pages"] == 1
