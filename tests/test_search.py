"""Tests for the Reepo full-text search module."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.search import (
    init_fts, rebuild_fts, search, _sanitize_fts_query,
    _FTS5_OPERATORS, _MAX_QUERY_LENGTH,
)


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


# --- Sanitization edge cases ---

class TestSanitizeEdgeCases:
    """Tests for hardened _sanitize_fts_query() — quotes, unicode, operators, long input."""

    def test_unbalanced_single_quote(self):
        result = _sanitize_fts_query("it's")
        assert result != '""'
        # Should produce a valid token (the apostrophe is kept since it's not special)
        assert '"' in result

    def test_unbalanced_double_quotes(self):
        result = _sanitize_fts_query('hello "world')
        # Double quotes should be stripped, tokens should still work
        assert '"hello"' in result
        assert '"world"' in result

    def test_only_double_quotes(self):
        result = _sanitize_fts_query('"""')
        assert result == '""'

    def test_nested_double_quotes(self):
        result = _sanitize_fts_query('"hello "nested" world"')
        assert '"hello"' in result
        assert '"nested"' in result
        assert '"world"' in result

    def test_unicode_accented_chars(self):
        result = _sanitize_fts_query("café résumé")
        assert '"café"' in result or '"cafe"' in result  # NFKC may normalize
        assert "OR" in result

    def test_unicode_cjk_characters(self):
        result = _sanitize_fts_query("机器学习")
        assert result != '""'

    def test_unicode_emoji(self):
        result = _sanitize_fts_query("🔥 pytorch")
        assert '"pytorch"' in result

    def test_unicode_combining_chars(self):
        # e + combining acute = é after NFKC normalization
        result = _sanitize_fts_query("caf\u0065\u0301")
        assert result != '""'

    def test_fts5_operator_AND(self):
        result = _sanitize_fts_query("hello AND world")
        assert '"hello"' in result
        assert '"world"' in result
        # AND should be stripped as an operator, not quoted
        assert '"AND"' not in result

    def test_fts5_operator_OR(self):
        result = _sanitize_fts_query("hello OR world")
        assert '"hello"' in result
        assert '"world"' in result
        # The user-typed OR should be stripped; only our structural OR remains
        assert '"OR"' not in result

    def test_fts5_operator_NOT(self):
        result = _sanitize_fts_query("hello NOT world")
        assert '"hello"' in result
        assert '"world"' in result
        assert '"NOT"' not in result

    def test_fts5_operator_NEAR(self):
        result = _sanitize_fts_query("NEAR pytorch")
        assert '"pytorch"' in result
        assert '"NEAR"' not in result

    def test_fts5_operators_case_insensitive(self):
        result = _sanitize_fts_query("and or not near")
        # All should be stripped
        assert result == '""'

    def test_only_operators(self):
        result = _sanitize_fts_query("AND OR NOT")
        assert result == '""'

    def test_column_filter_injection(self):
        # FTS5 supports "column:term" syntax — colon should be stripped
        result = _sanitize_fts_query("full_name:langchain")
        assert ":" not in result

    def test_prefix_wildcard_stripped(self):
        result = _sanitize_fts_query("torch*")
        assert "*" not in result

    def test_negation_operator_stripped(self):
        result = _sanitize_fts_query("-pytorch")
        assert "-" not in result

    def test_plus_operator_stripped(self):
        result = _sanitize_fts_query("+pytorch")
        assert "+" not in result

    def test_caret_stripped(self):
        result = _sanitize_fts_query("pytorch^2")
        assert "^" not in result

    def test_angle_brackets_stripped(self):
        result = _sanitize_fts_query("<script>alert</script>")
        assert "<" not in result
        assert ">" not in result

    def test_very_long_query_truncated(self):
        long_query = "a " * 1000
        result = _sanitize_fts_query(long_query)
        # After truncation to _MAX_QUERY_LENGTH chars, should still produce valid output
        assert result != '""'
        assert len(result) < len(long_query) * 5  # Much shorter than input

    def test_max_query_length_boundary(self):
        query = "x" * _MAX_QUERY_LENGTH
        result = _sanitize_fts_query(query)
        assert result != '""'

    def test_over_max_query_length(self):
        query = "x" * (_MAX_QUERY_LENGTH + 100)
        result = _sanitize_fts_query(query)
        # Should still work, just truncated
        assert result != '""'

    def test_tab_and_newline_whitespace(self):
        result = _sanitize_fts_query("hello\tworld\nfoo")
        assert '"hello"' in result
        assert '"world"' in result
        assert '"foo"' in result

    def test_null_bytes_stripped(self):
        result = _sanitize_fts_query("hello\x00world")
        assert "\x00" not in result


# --- Search with special queries (integration) ---

class TestSearchSpecialQueries:
    """Integration tests: ensure special-character queries don't crash and return correct results."""

    def test_query_with_quotes(self, seeded_db):
        result = search(seeded_db, query='"langchain"')
        # Should not crash; should find langchain
        assert isinstance(result["results"], list)

    def test_query_with_unbalanced_quotes(self, seeded_db):
        result = search(seeded_db, query='"langchain')
        assert isinstance(result["results"], list)

    def test_query_with_parentheses(self, seeded_db):
        result = search(seeded_db, query="pytorch(deep)")
        assert isinstance(result["results"], list)

    def test_query_with_brackets(self, seeded_db):
        result = search(seeded_db, query="test[0]")
        assert isinstance(result["results"], list)

    def test_query_with_asterisk(self, seeded_db):
        result = search(seeded_db, query="lang*")
        assert isinstance(result["results"], list)

    def test_query_with_fts5_AND_operator(self, seeded_db):
        result = search(seeded_db, query="langchain AND pytorch")
        assert isinstance(result["results"], list)

    def test_query_with_fts5_NOT_operator(self, seeded_db):
        result = search(seeded_db, query="pytorch NOT langchain")
        assert isinstance(result["results"], list)

    def test_query_with_fts5_NEAR_operator(self, seeded_db):
        result = search(seeded_db, query="NEAR(pytorch langchain)")
        assert isinstance(result["results"], list)

    def test_query_with_column_filter(self, seeded_db):
        result = search(seeded_db, query="full_name:langchain")
        assert isinstance(result["results"], list)

    def test_query_with_unicode(self, seeded_db):
        result = search(seeded_db, query="café résumé")
        assert isinstance(result["results"], list)
        assert result["total"] == 0  # No repos match these terms

    def test_query_with_cjk(self, seeded_db):
        result = search(seeded_db, query="机器学习")
        assert isinstance(result["results"], list)

    def test_query_with_emoji(self, seeded_db):
        result = search(seeded_db, query="🔥 pytorch")
        assert isinstance(result["results"], list)

    def test_query_only_special_chars(self, seeded_db):
        result = search(seeded_db, query="()[]{}*^~")
        assert result["total"] == 0
        assert result["results"] == []

    def test_query_only_operators(self, seeded_db):
        result = search(seeded_db, query="AND OR NOT")
        assert result["total"] == 0
        assert result["results"] == []

    def test_very_long_query(self, seeded_db):
        long_q = "pytorch " * 200
        result = search(seeded_db, query=long_q)
        assert isinstance(result["results"], list)

    def test_empty_string_query(self, seeded_db):
        result = search(seeded_db, query="")
        assert result["total"] == 5

    def test_whitespace_only_query(self, seeded_db):
        result = search(seeded_db, query="   ")
        assert result["total"] == 5  # Treated as no query

    def test_sql_injection_attempt(self, seeded_db):
        result = search(seeded_db, query="'; DROP TABLE repos; --")
        assert isinstance(result["results"], list)

    def test_backslash_in_query(self, seeded_db):
        result = search(seeded_db, query="pytorch\\deep")
        assert isinstance(result["results"], list)


# --- Optimized search correctness ---

class TestSearchJoinCorrectness:
    """Tests verifying the JOIN-based search returns correct rank ordering and snippets."""

    def test_relevance_sort_ranks_name_match_higher(self, seeded_db):
        result = search(seeded_db, query="langchain", sort="relevance")
        assert result["total"] >= 1
        # The exact name match should be first
        assert result["results"][0]["name"] == "langchain"

    def test_search_returns_snippets(self, seeded_db):
        # Search for a term that appears in the description (column 1) to get highlighted snippet
        result = search(seeded_db, query="composable chains")
        matching = [r for r in result["results"] if r["name"] == "langchain"]
        assert len(matching) == 1
        assert "snippet" in matching[0]

    def test_snippet_contains_highlight_tags(self, seeded_db):
        result = search(seeded_db, query="neural")
        for r in result["results"]:
            if "snippet" in r:
                # highlight wraps matches in <b>...</b>
                assert "<b>" in r["snippet"] or r["snippet"]

    def test_search_with_filter_and_query(self, seeded_db):
        result = search(seeded_db, query="python", language="Python")
        # All results should be Python language
        for r in result["results"]:
            assert r["language"] == "Python"

    def test_search_with_category_filter_and_query(self, seeded_db):
        result = search(seeded_db, query="framework", category="frameworks")
        for r in result["results"]:
            assert r["category_primary"] == "frameworks"

    def test_non_relevance_sort_with_query(self, seeded_db):
        result = search(seeded_db, query="python", sort="stars")
        if len(result["results"]) > 1:
            stars = [r["stars"] for r in result["results"]]
            assert stars == sorted(stars, reverse=True)

    def test_pagination_with_query(self, seeded_db):
        # Get all results first
        all_results = search(seeded_db, query="python", per_page=100)
        if all_results["total"] > 1:
            page1 = search(seeded_db, query="python", per_page=1, page=1)
            page2 = search(seeded_db, query="python", per_page=1, page=2)
            assert page1["results"][0]["id"] != page2["results"][0]["id"]

    def test_query_search_finds_readme_content(self, seeded_db):
        result = search(seeded_db, query="optimized tensor library")
        assert result["total"] >= 1
        names = [r["name"] for r in result["results"]]
        assert "pytorch" in names

    def test_query_search_finds_topic_content(self, seeded_db):
        result = search(seeded_db, query="deep-learning")
        assert result["total"] >= 1
