"""Reepo API — repo routes."""
import base64
import os
import re
import httpx
from fastapi import APIRouter, HTTPException, Query

from src.db import get_repo, list_repos, count_repos, _connect
from src.similar import find_similar
from src.middleware import detail_cache

router = APIRouter()

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")


def _truncate_readme(content: str, max_chars: int = 3000) -> str:
    """Truncate README to fit in a prompt."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n\n[truncated]"


def summarize_readme(readme_content: str, repo_name: str, description: str | None = None) -> str:
    """Use a local Ollama model to summarize a README into an About paragraph."""
    truncated = _truncate_readme(readme_content)
    desc_hint = f"\nGitHub description: {description}" if description else ""

    prompt = (
        f"Summarize this GitHub repo ({repo_name}) in 3-5 sentences. "
        f"State what it is and what problem it solves. Be direct and specific. "
        f"Do not reference that this is a repo or repository. Write as if describing the project itself. "
        f"Never use the words 'ultimately', 'essentially', 'comprehensive', or 'landscape'. "
        f"No marketing language. No quotes or markdown. Plain text only.{desc_hint}\n\n"
        f"README:\n{truncated}"
    )

    try:
        resp = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60.0,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception:
        pass
    return ""


@router.get("/api/repos")
def api_list_repos(
    category: str | None = Query(None),
    language: str | None = Query(None),
    min_score: int | None = Query(None, ge=0, le=100),
    sort_by: str = Query("stars"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    from src.server import get_db_path

    db_path = get_db_path()
    repos = list_repos(
        path=db_path, category=category, language=language,
        min_score=min_score, sort_by=sort_by, limit=limit, offset=offset,
    )
    total = count_repos(db_path)
    return {"repos": repos, "total": total}


@router.get("/api/repos/{owner}/{name}")
def api_get_repo(owner: str, name: str):
    from src.server import get_db_path

    db_path = get_db_path()

    cache_key = detail_cache.make_key("repo", owner=owner, name=name)
    cached = detail_cache.get(cache_key)
    if cached is not None:
        return cached

    repo = get_repo(owner, name, db_path)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    # Compute score percentile
    if repo.get("reepo_score") is not None:
        conn = _connect(db_path)
        row = conn.execute(
            "SELECT COUNT(*) AS below FROM repos WHERE reepo_score IS NOT NULL AND reepo_score < ?",
            (repo["reepo_score"],),
        ).fetchone()
        total_scored = conn.execute(
            "SELECT COUNT(*) AS cnt FROM repos WHERE reepo_score IS NOT NULL"
        ).fetchone()["cnt"]
        conn.close()
        if total_scored > 0:
            repo["score_percentile"] = round(row["below"] / total_scored * 100)

    from src.monetization.affiliates import get_affiliate_link
    affiliate = get_affiliate_link(repo["id"], path=db_path)
    if affiliate:
        repo["affiliate_link"] = {
            "provider": affiliate["provider"],
            "url": affiliate["url"],
            "link_id": affiliate["id"],
        }

    detail_cache.set(cache_key, repo, ttl=900)
    return repo


@router.get("/api/repos/{owner}/{name}/readme")
async def api_repo_readme(owner: str, name: str):
    """Get the README excerpt for a repo. Fetches from GitHub if not cached."""
    from src.server import get_db_path

    db_path = get_db_path()
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT readme_excerpt FROM repos WHERE owner = ? AND name = ?",
        (owner, name),
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Repo not found")

    excerpt = row[0] if isinstance(row, (tuple, list)) else row["readme_excerpt"]
    if excerpt:
        conn.close()
        return {"readme": excerpt}

    # Fetch README from GitHub and summarize with LLM
    url = f"https://api.github.com/repos/{owner}/{name}/readme"
    gh_headers = {"Accept": "application/vnd.github+json"}
    gh_token = os.environ.get("GITHUB_TOKEN")
    if gh_token:
        gh_headers["Authorization"] = f"Bearer {gh_token}"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=gh_headers)
            if resp.status_code == 200:
                data = resp.json()
                content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
                # Get description for context
                desc_row = conn.execute(
                    "SELECT description FROM repos WHERE owner = ? AND name = ?",
                    (owner, name),
                ).fetchone()
                description = desc_row["description"] if desc_row else None
                excerpt = summarize_readme(content, f"{owner}/{name}", description)
                if not excerpt:
                    excerpt = description or ""
                # Cache in DB
                conn.execute(
                    "UPDATE repos SET readme_excerpt = ? WHERE owner = ? AND name = ?",
                    (excerpt, owner, name),
                )
                conn.commit()
                conn.close()
                return {"readme": excerpt}
    except Exception:
        pass

    conn.close()
    return {"readme": None}


@router.get("/api/repos/{owner}/{name}/similar")
def api_similar_repos(
    owner: str,
    name: str,
    limit: int = Query(10, ge=1, le=50),
):
    from src.server import get_db_path

    db_path = get_db_path()
    results = find_similar(db_path, owner, name, limit=limit)
    return {"results": results, "total": len(results)}
