from fastapi import APIRouter, HTTPException, Query
from src.db import get_repo, get_score_history

router = APIRouter()


@router.get("/api/repos/{owner}/{name}/history")
def api_score_history(owner: str, name: str, limit: int = Query(30, ge=1, le=100)):
    from src.server import get_db_path
    db_path = get_db_path()
    repo = get_repo(owner, name, db_path)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    history = get_score_history(repo["id"], db_path)
    return {"history": [{"score": h["reepo_score"], "recorded_at": h["recorded_at"]} for h in history[:limit]]}
