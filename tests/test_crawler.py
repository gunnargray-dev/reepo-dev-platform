"""Tests for the Reepo GitHub crawler."""
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.crawler import (
    TOPICS,
    KEYWORDS,
    GITHUB_SEARCH_URL,
    PER_PAGE,
    MAX_PAGES,
    _build_headers,
    _extract_repo,
    _handle_rate_limit,
    _fetch_page,
    crawl_topic,
    crawl_keyword,
    crawl_all,
)


# --- Constants ---

class TestConstants:
    def test_topics_non_empty(self):
        assert len(TOPICS) > 0

    def test_topics_has_core_tags(self):
        core = {"machine-learning", "llm", "ai", "transformers", "pytorch", "tensorflow"}
        assert core.issubset(set(TOPICS))

    def test_keywords_non_empty(self):
        assert len(KEYWORDS) > 0

    def test_keywords_has_core(self):
        assert "ai framework" in KEYWORDS
        assert "llm tool" in KEYWORDS

    def test_search_url(self):
        assert GITHUB_SEARCH_URL == "https://api.github.com/search/repositories"

    def test_per_page(self):
        assert PER_PAGE == 100

    def test_max_pages(self):
        assert MAX_PAGES == 10

    def test_twenty_topics(self):
        assert len(TOPICS) == 20

    def test_four_keywords(self):
        assert len(KEYWORDS) == 4


# --- _build_headers ---

class TestBuildHeaders:
    def test_without_token(self):
        headers = _build_headers(None)
        assert "Accept" in headers
        assert "Authorization" not in headers

    def test_with_token(self):
        headers = _build_headers("ghp_test123")
        assert headers["Authorization"] == "Bearer ghp_test123"

    def test_accept_header(self):
        headers = _build_headers()
        assert "application/vnd.github+json" in headers["Accept"]

    def test_api_version(self):
        headers = _build_headers()
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"


# --- _extract_repo ---

class TestExtractRepo:
    def _make_github_item(self, **overrides):
        base = {
            "id": 12345,
            "owner": {"login": "test-org"},
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "description": "A test repository",
            "html_url": "https://github.com/test-org/test-repo",
            "stargazers_count": 1000,
            "forks_count": 100,
            "language": "Python",
            "license": {"spdx_id": "MIT"},
            "topics": ["ai", "ml"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "pushed_at": "2025-06-01T00:00:00Z",
            "open_issues_count": 50,
            "has_wiki": True,
            "homepage": "https://test.dev",
        }
        base.update(overrides)
        return base

    def test_extracts_github_id(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["github_id"] == 12345

    def test_extracts_owner(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["owner"] == "test-org"

    def test_extracts_name(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["name"] == "test-repo"

    def test_extracts_full_name(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["full_name"] == "test-org/test-repo"

    def test_extracts_description(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["description"] == "A test repository"

    def test_extracts_url(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["url"] == "https://github.com/test-org/test-repo"

    def test_extracts_stars(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["stars"] == 1000

    def test_extracts_forks(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["forks"] == 100

    def test_extracts_language(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["language"] == "Python"

    def test_extracts_license(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["license"] == "MIT"

    def test_extracts_topics(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["topics"] == ["ai", "ml"]

    def test_extracts_timestamps(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["created_at"] == "2024-01-01T00:00:00Z"
        assert repo["updated_at"] == "2025-01-01T00:00:00Z"
        assert repo["pushed_at"] == "2025-06-01T00:00:00Z"

    def test_extracts_open_issues(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["open_issues"] == 50

    def test_extracts_has_wiki(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["has_wiki"] is True

    def test_extracts_homepage(self):
        repo = _extract_repo(self._make_github_item())
        assert repo["homepage"] == "https://test.dev"

    def test_null_description(self):
        repo = _extract_repo(self._make_github_item(description=None))
        assert repo["description"] == ""

    def test_null_license(self):
        repo = _extract_repo(self._make_github_item(license=None))
        assert repo["license"] is None

    def test_null_language(self):
        repo = _extract_repo(self._make_github_item(language=None))
        assert repo["language"] is None

    def test_empty_topics(self):
        repo = _extract_repo(self._make_github_item(topics=[]))
        assert repo["topics"] == []

    def test_missing_homepage(self):
        item = self._make_github_item()
        del item["homepage"]
        repo = _extract_repo(item)
        assert repo["homepage"] is None


# --- _handle_rate_limit ---

class TestHandleRateLimit:
    @pytest.mark.asyncio
    async def test_no_sleep_when_remaining(self):
        response = MagicMock()
        response.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "0"}
        await _handle_rate_limit(response)  # Should not sleep

    @pytest.mark.asyncio
    async def test_sleeps_when_near_limit(self):
        response = MagicMock()
        reset_time = str(int(time.time()) + 2)
        response.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": reset_time}
        with patch("src.crawler.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await _handle_rate_limit(response)
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_sleep_duration(self):
        response = MagicMock()
        reset_time = str(int(time.time()) + 10)
        response.headers = {"X-RateLimit-Remaining": "1", "X-RateLimit-Reset": reset_time}
        with patch("src.crawler.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await _handle_rate_limit(response)
            if mock_sleep.called:
                wait = mock_sleep.call_args[0][0]
                assert wait >= 1


# --- Deduplication ---

class TestDeduplication:
    @pytest.mark.asyncio
    async def test_dedup_within_topic(self):
        items = [
            {"id": 1, "owner": {"login": "a"}, "name": "r1", "full_name": "a/r1",
             "description": "", "html_url": "", "stargazers_count": 10,
             "forks_count": 1, "language": "Python", "license": {"spdx_id": "MIT"},
             "topics": [], "created_at": "", "updated_at": "", "pushed_at": "",
             "open_issues_count": 0, "has_wiki": False, "homepage": ""},
            {"id": 1, "owner": {"login": "a"}, "name": "r1", "full_name": "a/r1",
             "description": "", "html_url": "", "stargazers_count": 10,
             "forks_count": 1, "language": "Python", "license": {"spdx_id": "MIT"},
             "topics": [], "created_at": "", "updated_at": "", "pushed_at": "",
             "open_issues_count": 0, "has_wiki": False, "homepage": ""},
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "0"}
        mock_response.json.return_value = {"items": items, "total_count": 2}

        with patch("src.crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            repos = await crawl_topic("test-topic", token="fake")
            assert len(repos) == 1

    @pytest.mark.asyncio
    async def test_dedup_across_topics(self):
        items = [
            {"id": 999, "owner": {"login": "org"}, "name": "repo", "full_name": "org/repo",
             "description": "test", "html_url": "", "stargazers_count": 100,
             "forks_count": 10, "language": "Python", "license": {"spdx_id": "MIT"},
             "topics": ["ai"], "created_at": "", "updated_at": "", "pushed_at": "",
             "open_issues_count": 5, "has_wiki": False, "homepage": ""},
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "0"}
        mock_response.json.return_value = {"items": items, "total_count": 1}

        with patch("src.crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("src.crawler.TOPICS", ["t1", "t2"]):
                with patch("src.crawler.KEYWORDS", []):
                    with patch("src.crawler.upsert_repo"):
                        with patch("src.crawler.init_db"):
                            count = await crawl_all(token="fake")
                            assert count == 1


# --- _fetch_page ---

class TestFetchPage:
    @pytest.mark.asyncio
    async def test_success(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "0"}
        mock_response.json.return_value = {"items": [{"id": 1}], "total_count": 1}
        mock_client.get.return_value = mock_response

        items, total = await _fetch_page(mock_client, "test", 1, {})
        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_422_returns_empty(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_client.get.return_value = mock_response

        items, total = await _fetch_page(mock_client, "bad query", 1, {})
        assert items == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_rate_limit_retry(self):
        mock_client = AsyncMock()

        rate_limited = MagicMock()
        rate_limited.status_code = 403
        rate_limited.headers = {"X-RateLimit-Reset": str(int(time.time()) + 1)}

        success = MagicMock()
        success.status_code = 200
        success.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "0"}
        success.json.return_value = {"items": [{"id": 1}], "total_count": 1}

        mock_client.get.side_effect = [rate_limited, success]

        with patch("src.crawler.asyncio.sleep", new_callable=AsyncMock):
            items, total = await _fetch_page(mock_client, "test", 1, {})
            assert len(items) == 1


# --- crawl_topic ---

class TestCrawlTopic:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "0"}
        mock_response.json.return_value = {"items": [], "total_count": 0}

        with patch("src.crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            repos = await crawl_topic("ai", token="fake")
            assert isinstance(repos, list)

    @pytest.mark.asyncio
    async def test_classifies_repos(self):
        items = [{
            "id": 555,
            "owner": {"login": "test"},
            "name": "pytorch-agent",
            "full_name": "test/pytorch-agent",
            "description": "An AI agent framework",
            "html_url": "",
            "stargazers_count": 100,
            "forks_count": 10,
            "language": "Python",
            "license": {"spdx_id": "MIT"},
            "topics": ["agents", "pytorch"],
            "created_at": "",
            "updated_at": "",
            "pushed_at": "",
            "open_issues_count": 5,
            "has_wiki": False,
            "homepage": "",
        }]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "0"}
        mock_response.json.return_value = {"items": items, "total_count": 1}

        with patch("src.crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            repos = await crawl_topic("agents", token="fake")
            assert len(repos) == 1
            assert repos[0]["category_primary"] is not None


# --- crawl_keyword ---

class TestCrawlKeyword:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "0"}
        mock_response.json.return_value = {"items": [], "total_count": 0}

        with patch("src.crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            repos = await crawl_keyword("ai framework", token="fake")
            assert isinstance(repos, list)


# --- crawl_all ---

class TestCrawlAll:
    @pytest.mark.asyncio
    async def test_returns_count(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "0"}
        mock_response.json.return_value = {"items": [], "total_count": 0}

        with patch("src.crawler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("src.crawler.init_db"):
                with patch("src.crawler.upsert_repo"):
                    count = await crawl_all(token="fake")
                    assert isinstance(count, int)
                    assert count == 0
