"""Tests for awesome import — parse markdown, handle malformed URLs, bulk import."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.growth.db import init_growth_db
from src.growth.awesome_import import parse_awesome_list, import_from_url, bulk_import


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_growth_db(path)
    yield path
    os.unlink(path)


SAMPLE_AWESOME_LIST = """
# Awesome AI Tools

## Frameworks
- [TensorFlow](https://github.com/tensorflow/tensorflow) - An open source ML framework
- [PyTorch](https://github.com/pytorch/pytorch) — A deep learning framework

## Tools
- [Hugging Face](https://github.com/huggingface/transformers) - State-of-the-art NLP
- [LangChain](https://github.com/langchain-ai/langchain) - Build LLM apps

## Not GitHub
- [Some Tool](https://gitlab.com/foo/bar) - Not on GitHub
"""


class TestParseAwesomeList:
    def test_parse_extracts_repos(self):
        results = parse_awesome_list(SAMPLE_AWESOME_LIST)
        assert len(results) == 4
        owners = [r["owner"] for r in results]
        assert "tensorflow" in owners
        assert "pytorch" in owners

    def test_parse_extracts_full_name(self):
        results = parse_awesome_list(SAMPLE_AWESOME_LIST)
        full_names = [r["full_name"] for r in results]
        assert "tensorflow/tensorflow" in full_names

    def test_parse_deduplicates(self):
        md = """
- [Repo](https://github.com/org/repo) - Description
- [Repo Again](https://github.com/org/repo) - Duplicate
"""
        results = parse_awesome_list(md)
        assert len(results) == 1

    def test_parse_empty_content(self):
        results = parse_awesome_list("")
        assert results == []

    def test_parse_no_github_links(self):
        results = parse_awesome_list("Just some text without any links.")
        assert results == []

    def test_parse_handles_trailing_slash(self):
        md = "- [Repo](https://github.com/org/repo/) - With slash"
        results = parse_awesome_list(md)
        assert len(results) == 1
        assert results[0]["name"] == "repo"

    def test_parse_ignores_non_github(self):
        md = "- [Tool](https://gitlab.com/org/repo) - GitLab"
        results = parse_awesome_list(md)
        assert len(results) == 0

    def test_parse_various_markdown_formats(self):
        md = """
* https://github.com/owner1/name1
- [Link](https://github.com/owner2/name2)
  - Nested https://github.com/owner3/name3 in text
"""
        results = parse_awesome_list(md)
        assert len(results) == 3


class TestImportFromUrl:
    def test_valid_url(self):
        result = import_from_url("https://raw.githubusercontent.com/sindresorhus/awesome/main/readme.md")
        assert result["ok"] is True

    def test_invalid_url(self):
        result = import_from_url("not-a-url")
        assert result["ok"] is False


class TestBulkImport:
    def test_import_new_repos(self, db_path):
        urls = [
            "https://github.com/org1/repo1",
            "https://github.com/org2/repo2",
        ]
        result = bulk_import(urls, db_path)
        assert result["imported"] == 2
        assert result["already_indexed"] == 0
        assert result["invalid"] == 0

    def test_import_with_existing(self, db_path):
        insert_repo({
            "github_id": 1, "owner": "org1", "name": "repo1",
            "full_name": "org1/repo1", "stars": 100,
            "language": "Python", "category_primary": "frameworks",
        }, db_path)
        urls = [
            "https://github.com/org1/repo1",
            "https://github.com/org2/repo2",
        ]
        result = bulk_import(urls, db_path)
        assert result["imported"] == 1
        assert result["already_indexed"] == 1

    def test_import_with_invalid_urls(self, db_path):
        urls = [
            "https://github.com/org1/repo1",
            "not-a-url",
            "https://gitlab.com/org/repo",
        ]
        result = bulk_import(urls, db_path)
        assert result["imported"] == 1
        assert result["invalid"] == 2

    def test_import_empty_list(self, db_path):
        result = bulk_import([], db_path)
        assert result["imported"] == 0
        assert result["already_indexed"] == 0
        assert result["invalid"] == 0

    def test_import_all_duplicates(self, db_path):
        urls = ["https://github.com/org1/repo1"]
        bulk_import(urls, db_path)
        result = bulk_import(urls, db_path)
        assert result["imported"] == 0
        assert result["already_indexed"] == 1
