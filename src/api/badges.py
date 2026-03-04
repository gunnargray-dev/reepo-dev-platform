"""Reepo API — badge SVG endpoint."""
from fastapi import APIRouter, Query, Response, HTTPException

router = APIRouter()


@router.get("/badge/{owner}/{name}.svg")
def api_get_badge(
    owner: str,
    name: str,
    style: str = Query("flat"),
):
    from src.server import get_db_path
    from src.growth.badges import get_badge_for_repo

    svg = get_badge_for_repo(owner, name, style=style, path=get_db_path())
    if svg is None:
        raise HTTPException(status_code=404, detail="Repo not found")
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "max-age=3600"},
    )
