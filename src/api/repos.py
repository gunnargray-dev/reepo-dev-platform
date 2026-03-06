"""Reepo API — repo routes."""
import base64
import httpx
from fastapi import APIRouter, HTTPException, Query

from src.db import get_repo, list_repos, count_repos, _connect
from src.similar import find_similar
from src.middleware import detail_cache

router = APIRouter()


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

    # Fetch from GitHub API
    url = f"https://api.github.com/repos/{owner}/{name}/readme"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"Accept": "application/vnd.github+json"})
            if resp.status_code == 200:
                data = resp.json()
                import re
                content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
                # Strip markdown to plain text excerpt
                lines = []
                for line in content.split("\n"):
                    stripped = line.strip()
                    # Skip empty, headings, images, HTML, tables, separators, badges
                    if not stripped:
                        continue
                    if stripped.startswith(("#", "![", "<!--", "<", "|", "---", "===", "```")):
                        continue
                    if stripped.startswith("[!") or stripped.startswith("[!["):
                        continue
                    # Remove inline markdown: links, bold, italic, code, HTML tags
                    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', stripped)  # [text](url) -> text
                    cleaned = re.sub(r'<a[^>]*>|</a>', '', cleaned)  # strip <a> tags
                    cleaned = re.sub(r'<[^>]+>', '', cleaned)  # strip HTML tags
                    cleaned = re.sub(r'[*_`~]+', '', cleaned)  # strip formatting chars
                    cleaned = cleaned.strip()
                    if not cleaned or len(cleaned) < 5:
                        continue
                    lines.append(cleaned)
                    if len(" ".join(lines)) > 500:
                        break
                excerpt = " ".join(lines)[:500]
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
