"""Reepo API — recommendation endpoints."""
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/api/recommendations")
def api_get_recommendations(
    user_id: int = Query(...),
    limit: int = Query(10, ge=1, le=50),
    method: str = Query("topic"),
):
    from src.server import get_db_path
    from src.growth.recommendations import (
        get_recommendations_for_user,
        get_collaborative_recommendations,
    )

    db_path = get_db_path()
    if method == "collaborative":
        recs = get_collaborative_recommendations(user_id, db_path, limit=limit)
    else:
        recs = get_recommendations_for_user(user_id, db_path, limit=limit)
    return {"recommendations": recs, "total": len(recs), "method": method}
