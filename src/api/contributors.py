"""Reepo API — contributor badges endpoint."""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/api/u/{username}/badges")
def api_user_badges(username: str, user_id: int | None = None):
    from src.server import get_db_path
    from src.community.contributors import get_user_badges

    # In a real system we'd resolve username -> user_id
    # For now, user_id is passed as a query param or defaults to username hash
    if user_id is None:
        return {"username": username, "badges": []}
    badges = get_user_badges(user_id, get_db_path())
    return {"username": username, "badges": badges}
