"""Reepo API — public stats endpoint for the stats page."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/public-stats")
def api_public_stats():
    from src.server import get_db_path
    from src.db import (
        _connect, count_repos, get_repos_by_category, get_repos_by_language,
        get_score_stats, list_repos,
    )

    db_path = get_db_path()
    conn = _connect(db_path)

    total_repos = count_repos(db_path)
    by_category = get_repos_by_category(db_path)
    by_language = get_repos_by_language(db_path, limit=20)
    score_stats = get_score_stats(db_path)

    # Median score
    median_row = conn.execute(
        "SELECT reepo_score FROM repos WHERE reepo_score IS NOT NULL "
        "ORDER BY reepo_score LIMIT 1 OFFSET (SELECT COUNT(*) / 2 FROM repos WHERE reepo_score IS NOT NULL)"
    ).fetchone()
    median_score = median_row["reepo_score"] if median_row else 0

    # Index growth (last 90 days via indexed_at)
    index_growth = [
        dict(r) for r in conn.execute(
            "SELECT DATE(indexed_at) as date, COUNT(*) as total_repos "
            "FROM repos WHERE indexed_at IS NOT NULL "
            "GROUP BY DATE(indexed_at) ORDER BY date DESC LIMIT 90"
        ).fetchall()
    ]

    # Top repos by score
    top_by_score = [
        dict(r) for r in conn.execute(
            "SELECT full_name, reepo_score, stars, language, category_primary "
            "FROM repos WHERE reepo_score IS NOT NULL ORDER BY reepo_score DESC LIMIT 10"
        ).fetchall()
    ]

    # Newest repos
    newest = [
        dict(r) for r in conn.execute(
            "SELECT full_name, description, stars, language, indexed_at "
            "FROM repos ORDER BY indexed_at DESC LIMIT 10"
        ).fetchall()
    ]

    conn.close()

    return {
        "total_repos": total_repos,
        "repos_by_category": by_category,
        "repos_by_language": by_language,
        "avg_reepo_score": score_stats["avg_score"],
        "median_score": median_score,
        "score_distribution": score_stats["distribution"],
        "index_growth": index_growth,
        "top_repos_by_score": top_by_score,
        "newest_repos": newest,
    }
