"""Tests for bot core — command parsing, execution, and response formatting."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo, get_categories
from src.search import init_fts
from src.trending import init_trending_tables
from src.bots.core import (
    parse_command, execute_command,
    format_slack_response, format_discord_response, format_plain_response,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_fts(path)
    init_trending_tables(path)
    yield path
    os.unlink(path)


@pytest.fixture
def seeded_db(db_path):
    insert_repo({
        "github_id": 1, "owner": "org1", "name": "repo1",
        "full_name": "org1/repo1", "description": "An AI framework",
        "stars": 5000, "language": "Python", "category_primary": "frameworks",
        "reepo_score": 85, "url": "https://github.com/org1/repo1",
    }, db_path)
    insert_repo({
        "github_id": 2, "owner": "org2", "name": "repo2",
        "full_name": "org2/repo2", "description": "Agent toolkit",
        "stars": 2000, "language": "TypeScript", "category_primary": "agents",
        "reepo_score": 72, "url": "https://github.com/org2/repo2",
    }, db_path)
    init_fts(db_path)
    return db_path


# --- parse_command ---

class TestParseCommand:
    def test_search(self):
        result = parse_command("/reepo search transformers")
        assert result["command"] == "search"
        assert result["query"] == "transformers"

    def test_search_multi_word(self):
        result = parse_command("/reepo search machine learning framework")
        assert result["command"] == "search"
        assert result["query"] == "machine learning framework"

    def test_search_no_query(self):
        result = parse_command("/reepo search")
        assert result["command"] == "error"

    def test_info(self):
        result = parse_command("/reepo info org/repo")
        assert result["command"] == "info"
        assert result["owner"] == "org"
        assert result["name"] == "repo"

    def test_info_no_slash(self):
        result = parse_command("/reepo info badformat")
        assert result["command"] == "error"

    def test_trending(self):
        result = parse_command("/reepo trending")
        assert result["command"] == "trending"
        assert result["category"] is None

    def test_trending_with_category(self):
        result = parse_command("/reepo trending frameworks")
        assert result["command"] == "trending"
        assert result["category"] == "frameworks"

    def test_compare(self):
        result = parse_command("/reepo compare org1/repo1 org2/repo2")
        assert result["command"] == "compare"
        assert len(result["repos"]) == 2

    def test_compare_insufficient(self):
        result = parse_command("/reepo compare org/repo")
        assert result["command"] == "error"

    def test_categories(self):
        result = parse_command("/reepo categories")
        assert result["command"] == "categories"

    def test_help(self):
        result = parse_command("/reepo help")
        assert result["command"] == "help"

    def test_empty_input(self):
        result = parse_command("")
        assert result["command"] == "help"

    def test_just_reepo(self):
        result = parse_command("/reepo")
        assert result["command"] == "help"

    def test_unknown_command(self):
        result = parse_command("/reepo foobar")
        assert result["command"] == "unknown"

    def test_without_slash_prefix(self):
        result = parse_command("search llm")
        assert result["command"] == "search"
        assert result["query"] == "llm"

    def test_case_insensitive_prefix(self):
        result = parse_command("/REEPO help")
        assert result["command"] == "help"

    def test_extra_whitespace(self):
        result = parse_command("  /reepo   search   ai  ")
        assert result["command"] == "search"
        assert result["query"] == "ai"

    def test_info_with_dots_and_dashes(self):
        result = parse_command("/reepo info my-org/my.repo-v2")
        assert result["command"] == "info"
        assert result["owner"] == "my-org"
        assert result["name"] == "my.repo-v2"


# --- execute_command ---

class TestExecuteCommand:
    def test_help(self, db_path):
        result = execute_command({"command": "help"}, db_path)
        assert result["command"] == "help"
        assert "search" in result["text"].lower()

    def test_error(self, db_path):
        result = execute_command({"command": "error", "message": "Bad"}, db_path)
        assert result["command"] == "error"
        assert result["text"] == "Bad"

    def test_unknown(self, db_path):
        result = execute_command({"command": "unknown", "text": "foo"}, db_path)
        assert result["command"] == "error"

    def test_search_with_results(self, seeded_db):
        result = execute_command({"command": "search", "query": "AI"}, seeded_db)
        assert result["command"] == "search"
        assert result["total"] >= 1
        assert len(result["repos"]) >= 1

    def test_search_no_results(self, seeded_db):
        result = execute_command({"command": "search", "query": "zzzznonexistent"}, seeded_db)
        assert result["command"] == "search"
        assert result["total"] == 0

    def test_info_found(self, seeded_db):
        result = execute_command({"command": "info", "owner": "org1", "name": "repo1"}, seeded_db)
        assert result["command"] == "info"
        assert result["repo"]["full_name"] == "org1/repo1"
        assert result["repo"]["stars"] == 5000

    def test_info_not_found(self, seeded_db):
        result = execute_command({"command": "info", "owner": "x", "name": "y"}, seeded_db)
        assert result["command"] == "error"

    def test_trending(self, seeded_db):
        result = execute_command({"command": "trending", "category": None}, seeded_db)
        assert result["command"] == "trending"
        assert isinstance(result["repos"], list)

    def test_trending_with_category(self, seeded_db):
        result = execute_command({"command": "trending", "category": "frameworks"}, seeded_db)
        assert result["command"] == "trending"

    def test_compare_found(self, seeded_db):
        result = execute_command({"command": "compare", "repos": ["org1/repo1", "org2/repo2"]}, seeded_db)
        assert result["command"] == "compare"
        assert len(result["repos"]) == 2

    def test_compare_not_found(self, seeded_db):
        result = execute_command({"command": "compare", "repos": ["org1/repo1", "x/y"]}, seeded_db)
        assert result["command"] == "error"

    def test_categories(self, seeded_db):
        result = execute_command({"command": "categories"}, seeded_db)
        assert result["command"] == "categories"
        assert len(result["categories"]) > 0


# --- format_slack_response ---

class TestFormatSlackResponse:
    def test_help(self):
        resp = format_slack_response({"command": "help", "text": "Help text"})
        assert resp["response_type"] == "in_channel"
        assert len(resp["blocks"]) > 0
        assert resp["blocks"][0]["text"]["text"] == "Help text"

    def test_error(self):
        resp = format_slack_response({"command": "error", "text": "Something went wrong"})
        assert resp["blocks"][0]["text"]["text"] == "Something went wrong"

    def test_search(self):
        resp = format_slack_response({
            "command": "search", "query": "test", "total": 1,
            "repos": [{"full_name": "org/repo", "description": "Desc", "stars": 100, "reepo_score": 80}],
        })
        assert "search" in resp["blocks"][0]["text"]["text"].lower()
        assert len(resp["blocks"]) >= 2

    def test_info(self):
        resp = format_slack_response({
            "command": "info",
            "repo": {"full_name": "org/repo", "description": "D", "stars": 100, "forks": 10,
                     "reepo_score": 80, "language": "Python", "license": "MIT", "category": "frameworks"},
        })
        assert "org/repo" in resp["blocks"][0]["text"]["text"]

    def test_trending_empty(self):
        resp = format_slack_response({"command": "trending", "category": None, "repos": []})
        assert any("No trending" in b["text"]["text"] for b in resp["blocks"])

    def test_compare(self):
        resp = format_slack_response({
            "command": "compare",
            "repos": [
                {"full_name": "a/b", "stars": 100, "forks": 10, "reepo_score": 80, "language": "Py"},
                {"full_name": "c/d", "stars": 200, "forks": 20, "reepo_score": 90, "language": "Go"},
            ],
        })
        assert "Comparison" in resp["blocks"][0]["text"]["text"]

    def test_categories(self):
        resp = format_slack_response({
            "command": "categories",
            "categories": [{"name": "Frameworks", "slug": "frameworks", "repo_count": 42}],
        })
        assert "Categories" in resp["blocks"][0]["text"]["text"]


# --- format_discord_response ---

class TestFormatDiscordResponse:
    def test_help(self):
        resp = format_discord_response({"command": "help", "text": "Help text"})
        assert resp["type"] == 4
        assert resp["data"]["embeds"][0]["title"] == "Reepo Bot"

    def test_error(self):
        resp = format_discord_response({"command": "error", "text": "Error"})
        assert resp["data"]["embeds"][0]["color"] == 0xe05d44

    def test_search(self):
        resp = format_discord_response({
            "command": "search", "query": "test", "total": 1,
            "repos": [{"full_name": "org/repo", "stars": 100, "reepo_score": 80}],
        })
        assert "test" in resp["data"]["embeds"][0]["title"].lower()

    def test_info(self):
        resp = format_discord_response({
            "command": "info",
            "repo": {"full_name": "org/repo", "description": "D", "stars": 100, "forks": 10,
                     "reepo_score": 80, "language": "Python", "license": "MIT", "category": "frameworks"},
        })
        assert resp["data"]["embeds"][0]["title"] == "org/repo"
        assert len(resp["data"]["embeds"][0]["fields"]) == 6

    def test_trending(self):
        resp = format_discord_response({
            "command": "trending", "category": "frameworks",
            "repos": [{"full_name": "a/b", "stars": 100, "star_delta": 50, "reepo_score": 80}],
        })
        assert "frameworks" in resp["data"]["embeds"][0]["title"].lower()

    def test_compare(self):
        resp = format_discord_response({
            "command": "compare",
            "repos": [
                {"full_name": "a/b", "stars": 100, "forks": 10, "reepo_score": 80, "language": "Py"},
                {"full_name": "c/d", "stars": 200, "forks": 20, "reepo_score": 90, "language": "Go"},
            ],
        })
        assert "Comparison" in resp["data"]["embeds"][0]["title"]

    def test_categories(self):
        resp = format_discord_response({
            "command": "categories",
            "categories": [{"name": "Frameworks", "slug": "frameworks", "repo_count": 42}],
        })
        assert "Categories" in resp["data"]["embeds"][0]["title"]


# --- format_plain_response ---

class TestFormatPlainResponse:
    def test_help(self):
        text = format_plain_response({"command": "help", "text": "Help"})
        assert text == "Help"

    def test_search(self):
        text = format_plain_response({
            "command": "search", "query": "test", "total": 1,
            "repos": [{"full_name": "org/repo", "stars": 100, "reepo_score": 80}],
        })
        assert "org/repo" in text

    def test_info(self):
        text = format_plain_response({
            "command": "info",
            "repo": {"full_name": "org/repo", "description": "Desc", "stars": 100, "forks": 10,
                     "reepo_score": 80, "language": "Python", "license": "MIT"},
        })
        assert "org/repo" in text
        assert "100" in text

    def test_trending(self):
        text = format_plain_response({
            "command": "trending", "category": None,
            "repos": [{"full_name": "a/b", "stars": 100, "star_delta": 50, "reepo_score": 80}],
        })
        assert "Trending" in text

    def test_compare(self):
        text = format_plain_response({
            "command": "compare",
            "repos": [
                {"full_name": "a/b", "stars": 100, "forks": 10, "reepo_score": 80},
                {"full_name": "c/d", "stars": 200, "forks": 20, "reepo_score": 90},
            ],
        })
        assert "Comparison" in text

    def test_categories(self):
        text = format_plain_response({
            "command": "categories",
            "categories": [{"name": "Frameworks", "slug": "frameworks", "repo_count": 42}],
        })
        assert "Frameworks" in text

    def test_fallback(self):
        text = format_plain_response({"command": "nonexistent"})
        assert "No results" in text
