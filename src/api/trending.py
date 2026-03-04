"""Reepo API — trending routes."""
from fastapi import APIRouter, Query

from src.trending import get_trending, get_new_repos

router = APIRouter()


@router.get("/api/trending")
def api_trending(
    period: str = Query("week", description="Period: day, week, month"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    from src.server import get_db_path

    db_path = get_db_path()
    results = get_trending(db_path, period=period, limit=limit)
    return {"results": results, "period": period, "total": len(results)}


@router.get("/api/trending/new")
def api_new_repos(
    days: int = Query(7, ge=1, le=90, description="Days back to look"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    from src.server import get_db_path

    db_path = get_db_path()
    results = get_new_repos(db_path, days=days, limit=limit)
    return {"results": results, "total": len(results)}
