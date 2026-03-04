"""Reepo API — export routes (Pro only)."""
from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter()


@router.get("/api/export/search")
def export_search(
    q: str = Query("", description="Search query"),
    format: str = Query("json", description="Export format: json or csv"),
    user_id: int | None = Query(None, description="User ID for pro check"),
):
    from src.server import get_db_path
    from src.monetization.gates import require_pro
    from src.search import search

    db_path = get_db_path()
    require_pro(user_id, path=db_path)

    result = search(path=db_path, query=q, page=1, per_page=100)
    repos = result["results"]

    if format == "csv":
        return _repos_to_csv(repos)
    return {"repos": repos, "total": len(repos)}


@router.get("/api/export/repo/{owner}/{name}")
def export_repo(
    owner: str,
    name: str,
    format: str = Query("json", description="Export format: json"),
    user_id: int | None = Query(None, description="User ID for pro check"),
):
    from src.server import get_db_path
    from src.monetization.gates import require_pro
    from src.db import get_repo
    from src.similar import find_similar
    from src.db import get_score_history

    db_path = get_db_path()
    require_pro(user_id, path=db_path)

    repo = get_repo(owner, name, db_path)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    similar = find_similar(db_path, owner, name, limit=5)
    history = get_score_history(repo["id"], db_path)

    return {
        "repo": repo,
        "similar_repos": similar,
        "score_history": history,
    }


def _repos_to_csv(repos: list[dict]) -> Response:
    """Convert repos list to CSV response."""
    output = io.StringIO()
    if not repos:
        return Response(content="", media_type="text/csv")

    fields = ["full_name", "description", "stars", "forks", "language", "license", "reepo_score", "category_primary"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for repo in repos:
        writer.writerow(repo)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reepo_export.csv"},
    )
