"""Reepo API — stats routes."""
from fastapi import APIRouter

from src.db import count_repos, get_repos_by_category, get_repos_by_language, get_score_stats

router = APIRouter()


@router.get("/api/stats")
def api_stats():
    from src.server import get_db_path

    db_path = get_db_path()
    total = count_repos(db_path)
    by_category = get_repos_by_category(db_path)
    by_language = get_repos_by_language(db_path, limit=15)
    score_stats = get_score_stats(db_path)

    return {
        "total_repos": total,
        "by_category": by_category,
        "by_language": by_language,
        "score_stats": score_stats,
    }
