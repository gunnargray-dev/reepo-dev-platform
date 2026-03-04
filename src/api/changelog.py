"""Reepo API — repo changelog endpoint."""
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/api/repos/{owner}/{name}/changelog")
def api_get_changelog(
    owner: str,
    name: str,
    limit: int = Query(20, ge=1, le=100),
):
    from src.server import get_db_path
    from src.db import get_repo
    from src.growth.changelog import get_repo_changelog

    db_path = get_db_path()
    repo = get_repo(owner, name, db_path)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    events = get_repo_changelog(repo["id"], limit=limit, path=db_path)
    return {"events": events, "total": len(events)}
