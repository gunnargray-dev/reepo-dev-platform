"""Extract repo-specific use cases using Haiku LLM."""
import asyncio
import base64
import json
import logging
import os
import time

import anthropic
import httpx

from src.db import _connect, DEFAULT_DB_PATH

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """Given this GitHub repository, extract 3-4 specific use cases that describe what someone can BUILD or DO with it. Be concrete and specific to this repo — not generic AI/ML descriptions.

Repository: {full_name}
Description: {description}

README (first 3000 chars):
{readme}

Rules:
- Each use case should be a short phrase (8-15 words)
- Start each with an action verb (Build, Create, Deploy, Automate, etc.)
- Be specific to THIS repo's capabilities, not generic
- Skip install instructions, system requirements, licensing info
- If the repo is a library/framework, describe what users build WITH it
- If it's an app, describe what users can DO with it

Return ONLY a JSON array of strings, nothing else. Example:
["Build real-time object detection pipelines for video streams", "Train custom models on your own labeled dataset", "Deploy models as REST APIs with one command"]"""


async def fetch_readme(
    owner: str,
    name: str,
    client: httpx.AsyncClient,
    headers: dict,
) -> str | None:
    """Fetch README content from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{name}/readme"
    try:
        resp = await client.get(url, headers={**headers, "Accept": "application/vnd.github+json"})
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("content", "")
            encoding = data.get("encoding", "")
            if encoding == "base64" and content:
                return base64.b64decode(content).decode("utf-8", errors="replace")
        remaining = int(resp.headers.get("X-RateLimit-Remaining", "100"))
        if remaining <= 5:
            reset_at = int(resp.headers.get("X-RateLimit-Reset", "0"))
            wait = max(reset_at - int(time.time()), 1)
            if wait > 120:
                logger.warning("GitHub rate limit exhausted, stopping")
                return None
            logger.warning("Rate limit low (%d), sleeping %d seconds", remaining, wait)
            await asyncio.sleep(wait)
    except Exception as e:
        logger.debug("Failed to fetch README for %s/%s: %s", owner, name, e)
    return None


def extract_use_cases_llm(
    full_name: str,
    description: str,
    readme: str,
    client: anthropic.Anthropic,
) -> list[str]:
    """Call Haiku to extract use cases from a repo's README."""
    prompt = EXTRACT_PROMPT.format(
        full_name=full_name,
        description=description or "(no description)",
        readme=readme[:3000] if readme else "(no README)",
    )
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        # Parse JSON array from response
        # Handle cases where model wraps in markdown code block
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            text = text.rsplit("```", 1)[0]
        cases = json.loads(text)
        if isinstance(cases, list):
            return [str(c) for c in cases[:4] if c and len(str(c)) > 10]
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.debug("Failed to parse use cases for %s: %s", full_name, e)
    except anthropic.APIError as e:
        logger.warning("Anthropic API error for %s: %s", full_name, e)
    return []


async def extract_use_cases_batch(
    db_path: str = DEFAULT_DB_PATH,
    batch_size: int = 100,
    github_token: str | None = None,
    anthropic_key: str | None = None,
) -> int:
    """Fetch READMEs and extract use cases for repos missing them."""
    api_key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY required for use case extraction")
        return 0

    conn = _connect(db_path)

    # Add column if missing
    cols = [row[1] for row in conn.execute("PRAGMA table_info(repos)").fetchall()]
    if "use_cases" not in cols:
        conn.execute("ALTER TABLE repos ADD COLUMN use_cases TEXT")
        conn.commit()

    rows = conn.execute(
        "SELECT id, owner, name, full_name, description, readme_excerpt FROM repos "
        "WHERE use_cases IS NULL ORDER BY stars DESC LIMIT ?",
        (batch_size,),
    ).fetchall()
    conn.close()

    if not rows:
        logger.info("No repos need use case extraction")
        return 0

    gh_headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if github_token:
        gh_headers["Authorization"] = f"Bearer {github_token}"

    ai_client = anthropic.Anthropic(api_key=api_key)
    processed = 0

    async with httpx.AsyncClient(timeout=15.0) as http_client:
        for row in rows:
            repo_id = row["id"]
            owner = row["owner"]
            name = row["name"]
            full_name = row["full_name"]
            description = row["description"]
            cached_excerpt = row["readme_excerpt"]

            # Use cached readme_excerpt if available, else fetch from GitHub
            if cached_excerpt:
                readme = cached_excerpt
            else:
                readme = await fetch_readme(owner, name, http_client, gh_headers)
            cases = extract_use_cases_llm(full_name, description, readme, ai_client)

            conn = _connect(db_path)
            conn.execute(
                "UPDATE repos SET use_cases = ? WHERE id = ?",
                (json.dumps(cases), repo_id),
            )
            conn.commit()
            conn.close()

            processed += 1
            if processed % 25 == 0:
                logger.info("Processed %d/%d repos", processed, len(rows))

    logger.info("Use case extraction complete: %d repos processed", processed)
    return processed
