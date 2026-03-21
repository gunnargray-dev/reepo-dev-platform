"""Reepo Score API — score any GitHub repo on the fly."""
import os
import re

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.analyzer import analyze_repo
from src.taxonomy import classify_repo
from src.db import upsert_repo
from src.server import get_db_path

router = APIRouter()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


class ScoreRequest(BaseModel):
    url: str


def _parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner/name from a GitHub URL or owner/name string."""
    url = url.strip().rstrip("/")
    # Handle full URLs
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if match:
        return match.group(1), match.group(2)
    # Handle owner/name format
    match = re.match(r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$", url)
    if match:
        return match.group(1), match.group(2)
    raise ValueError("Invalid GitHub URL or owner/name")


def _extract_repo(item: dict) -> dict:
    """Extract repo dict from GitHub API response."""
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


@router.post("/api/score")
async def score_repo(req: ScoreRequest):
    """Score any GitHub repo on the fly."""
    try:
        owner, name = _parse_github_url(req.url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL. Use https://github.com/owner/name or owner/name")

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"https://api.github.com/repos/{owner}/{name}", headers=headers)

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Repository not found on GitHub")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch repo from GitHub")

    repo = _extract_repo(resp.json())
    primary, secondary = classify_repo(repo["name"], repo["description"], repo["topics"])
    result = analyze_repo(repo)

    # Persist to DB so the repo is searchable and can be featured
    repo["category_primary"] = primary
    repo["category_secondary"] = secondary
    repo["reepo_score"] = result["reepo_score"]
    repo["score_breakdown"] = result["score_breakdown"]
    repo_id = upsert_repo(repo, path=get_db_path())

    return {
        "repo": {
            "id": repo_id,
            "owner": repo["owner"],
            "name": repo["name"],
            "full_name": repo["full_name"],
            "description": repo["description"],
            "url": repo["url"],
            "stars": repo["stars"],
            "forks": repo["forks"],
            "language": repo["language"],
            "license": repo["license"],
            "category": primary,
        },
        "reepo_score": result["reepo_score"],
        "score_breakdown": result["score_breakdown"],
    }
