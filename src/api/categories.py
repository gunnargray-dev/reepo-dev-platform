"""Reepo API — category routes."""
from fastapi import APIRouter, Query

from src.db import get_categories, get_repos_by_category, list_repos

router = APIRouter()


@router.get("/api/categories")
def api_categories():
    from src.server import get_db_path

    db_path = get_db_path()
    categories = get_categories(db_path)
    counts = get_repos_by_category(db_path)

    for cat in categories:
        cat["repo_count"] = counts.get(cat["slug"], 0)

    return {"categories": categories}


@router.get("/api/categories/{slug}/repos")
def api_category_repos(
    slug: str,
    sort_by: str = Query("stars"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    from src.server import get_db_path

    db_path = get_db_path()
    repos = list_repos(path=db_path, category=slug, sort_by=sort_by, limit=limit, offset=offset)
    return {"repos": repos, "category": slug, "count": len(repos)}
