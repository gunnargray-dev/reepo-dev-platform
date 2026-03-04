"""Reepo API — search routes."""
from fastapi import APIRouter, Query

from src.middleware import search_cache
from src.search import search

router = APIRouter()


@router.get("/api/search")
def api_search(
    q: str = Query("", description="Search query"),
    category: str | None = Query(None, description="Filter by category"),
    language: str | None = Query(None, description="Filter by language"),
    min_score: int = Query(0, ge=0, le=100, description="Minimum Reepo Score"),
    sort: str = Query("relevance", description="Sort by: relevance, stars, score, newest"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
):
    from src.server import get_db_path

    db_path = get_db_path()

    cache_key = search_cache.make_key(
        "search", q=q, category=category, language=language,
        min_score=min_score, sort=sort, page=page, per_page=per_page,
    )
    cached = search_cache.get(cache_key)
    if cached is not None:
        return cached

    result = search(
        path=db_path,
        query=q,
        category=category,
        language=language,
        min_score=min_score,
        sort=sort,
        page=page,
        per_page=per_page,
    )

    search_cache.set(cache_key, result, ttl=300)
    return result
