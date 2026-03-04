"""Reepo API — repo routes."""
from fastapi import APIRouter, HTTPException, Query

from src.db import get_repo, list_repos, count_repos
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

    detail_cache.set(cache_key, repo, ttl=900)
    return repo


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
