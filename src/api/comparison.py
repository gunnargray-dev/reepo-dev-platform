"""Reepo API — comparison routes (Pro only)."""
from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.post("/api/compare")
def compare_repos(
    repo_ids: str = Query(..., description="Comma-separated repo IDs (2-5)"),
    user_id: int | None = Query(None, description="User ID for pro check"),
):
    from src.server import get_db_path
    from src.monetization.gates import require_pro
    from src.db import get_repo_by_id

    db_path = get_db_path()
    require_pro(user_id, path=db_path)

    ids = [int(x.strip()) for x in repo_ids.split(",") if x.strip()]
    if len(ids) < 2 or len(ids) > 5:
        raise HTTPException(status_code=400, detail="Provide 2-5 repo IDs")

    repos = []
    for rid in ids:
        repo = get_repo_by_id(rid, path=db_path)
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repo {rid} not found")
        comparison = {
            "id": repo["id"],
            "full_name": repo["full_name"],
            "description": repo.get("description"),
            "stars": repo.get("stars", 0),
            "forks": repo.get("forks", 0),
            "reepo_score": repo.get("reepo_score"),
            "score_breakdown": repo.get("score_breakdown"),
            "language": repo.get("language"),
            "license": repo.get("license"),
            "open_issues": repo.get("open_issues", 0),
            "category_primary": repo.get("category_primary"),
            "updated_at": repo.get("updated_at"),
            "pushed_at": repo.get("pushed_at"),
            "created_at": repo.get("created_at"),
            "topics": repo.get("topics", []),
        }
        repos.append(comparison)

    return {"repos": repos, "count": len(repos)}
