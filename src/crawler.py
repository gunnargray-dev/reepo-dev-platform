"""Reepo GitHub crawler — discover AI repos via GitHub Search API."""
import asyncio
import logging
import time

import httpx

from src.db import init_db, upsert_repo, DEFAULT_DB_PATH
from src.taxonomy import classify_repo

logger = logging.getLogger(__name__)

TOPICS = [
    "machine-learning", "llm", "ai", "langchain", "agents",
    "transformers", "openai", "computer-vision", "nlp", "rag",
    "vector-database", "mlops", "deep-learning", "pytorch",
    "tensorflow", "huggingface", "stable-diffusion", "gpt",
    "chatbot", "embedding",
]

KEYWORDS = [
    "ai framework",
    "llm tool",
    "agent framework",
    "ml pipeline",
]

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
PER_PAGE = 100
MAX_PAGES = 10  # 1000 results max per query


def _build_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _extract_repo(item: dict) -> dict:
    license_info = item.get("license") or {}
    return {
        "github_id": item["id"],
        "owner": item["owner"]["login"],
        "name": item["name"],
        "full_name": item["full_name"],
        "description": item.get("description") or "",
        "url": item["html_url"],
        "stars": item.get("stargazers_count", 0),
        "forks": item.get("forks_count", 0),
        "language": item.get("language"),
        "license": license_info.get("spdx_id"),
        "topics": item.get("topics", []),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "pushed_at": item.get("pushed_at"),
        "open_issues": item.get("open_issues_count", 0),
        "has_wiki": item.get("has_wiki", False),
        "homepage": item.get("homepage"),
    }


async def _handle_rate_limit(response: httpx.Response) -> None:
    remaining = int(response.headers.get("X-RateLimit-Remaining", "1"))
    if remaining <= 1:
        reset_at = int(response.headers.get("X-RateLimit-Reset", "0"))
        wait = max(reset_at - int(time.time()), 1)
        logger.warning("Rate limit nearly exhausted, sleeping %d seconds", wait)
        await asyncio.sleep(wait)


async def _fetch_page(
    client: httpx.AsyncClient,
    query: str,
    page: int,
    headers: dict[str, str],
) -> tuple[list[dict], int]:
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": PER_PAGE,
        "page": page,
    }

    backoff = 1
    for attempt in range(5):
        response = await client.get(
            GITHUB_SEARCH_URL, params=params, headers=headers
        )

        if response.status_code == 200:
            await _handle_rate_limit(response)
            data = response.json()
            return data.get("items", []), data.get("total_count", 0)

        if response.status_code in (403, 429):
            reset_at = int(response.headers.get("X-RateLimit-Reset", "0"))
            wait = max(reset_at - int(time.time()), backoff)
            logger.warning(
                "Rate limited (attempt %d), sleeping %d seconds",
                attempt + 1,
                wait,
            )
            await asyncio.sleep(wait)
            backoff *= 2
            continue

        if response.status_code == 422:
            logger.warning("Unprocessable query: %s", query)
            return [], 0

        if response.status_code >= 500:
            logger.warning(
                "Server error %d (attempt %d), retrying in %d seconds",
                response.status_code, attempt + 1, backoff,
            )
            await asyncio.sleep(backoff)
            backoff *= 2
            continue

        response.raise_for_status()

    logger.error("Exhausted retries for query: %s page %d", query, page)
    return [], 0


async def crawl_topic(
    topic: str,
    token: str | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> list[dict]:
    """Crawl repos for a single topic tag. Returns list of extracted repo dicts."""
    query = f"topic:{topic} stars:>5"
    headers = _build_headers(token)
    seen_ids: set[int] = set()
    repos: list[dict] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for page in range(1, MAX_PAGES + 1):
            items, total = await _fetch_page(client, query, page, headers)
            if not items:
                break

            for item in items:
                gid = item["id"]
                if gid in seen_ids:
                    continue
                seen_ids.add(gid)
                repo = _extract_repo(item)
                primary, secondary = classify_repo(
                    repo["name"],
                    repo["description"],
                    repo["topics"],
                )
                repo["category_primary"] = primary
                repo["categories_secondary"] = secondary
                repos.append(repo)

            if page * PER_PAGE >= min(total, 1000):
                break

    return repos


async def crawl_keyword(
    keyword: str,
    token: str | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> list[dict]:
    """Crawl repos for a keyword search. Returns list of extracted repo dicts."""
    query = f"{keyword} in:name,description stars:>10"
    headers = _build_headers(token)
    seen_ids: set[int] = set()
    repos: list[dict] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for page in range(1, MAX_PAGES + 1):
            items, total = await _fetch_page(client, query, page, headers)
            if not items:
                break

            for item in items:
                gid = item["id"]
                if gid in seen_ids:
                    continue
                seen_ids.add(gid)
                repo = _extract_repo(item)
                primary, secondary = classify_repo(
                    repo["name"],
                    repo["description"],
                    repo["topics"],
                )
                repo["category_primary"] = primary
                repo["categories_secondary"] = secondary
                repos.append(repo)

            if page * PER_PAGE >= min(total, 1000):
                break

    return repos


async def crawl_all(
    token: str | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Crawl all topics and keywords, store in DB. Returns total new repos found."""
    init_db(db_path)
    seen_ids: set[int] = set()
    new_count = 0

    for topic in TOPICS:
        logger.info("Crawling topic: %s", topic)
        repos = await crawl_topic(topic, token, db_path)
        for repo in repos:
            gid = repo["github_id"]
            if gid not in seen_ids:
                seen_ids.add(gid)
                upsert_repo(repo, db_path)
                new_count += 1
        logger.info("  %s: +%d repos (total: %d)", topic, len(repos), new_count)

    for keyword in KEYWORDS:
        logger.info("Crawling keyword: %s", keyword)
        repos = await crawl_keyword(keyword, token, db_path)
        for repo in repos:
            gid = repo["github_id"]
            if gid not in seen_ids:
                seen_ids.add(gid)
                upsert_repo(repo, db_path)
                new_count += 1
        logger.info("  %s: +%d repos (total: %d)", keyword, len(repos), new_count)

    logger.info("Crawl complete: %d repos indexed", new_count)
    return new_count
