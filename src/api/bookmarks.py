"""Reepo API — bookmark endpoints."""
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


@router.post("/{repo_id}")
def add_bookmark_endpoint(repo_id: int, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import add_bookmark

    payload = require_auth(request)
    ok = add_bookmark(payload["sub"], repo_id, get_db_path())
    if not ok:
        raise HTTPException(status_code=409, detail="Already bookmarked")
    return {"bookmarked": True}


@router.delete("/{repo_id}")
def remove_bookmark_endpoint(repo_id: int, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import remove_bookmark

    payload = require_auth(request)
    ok = remove_bookmark(payload["sub"], repo_id, get_db_path())
    if not ok:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"removed": True}


@router.get("/check")
def check_bookmarks_endpoint(request: Request, repo_ids: str = ""):
    """Check which repo IDs are bookmarked by the current user."""
    from src.server import get_db_path
    from src.auth.middleware import require_auth

    payload = require_auth(request)
    user_id = payload["sub"]

    ids = [int(x.strip()) for x in repo_ids.split(",") if x.strip().isdigit()]
    if not ids:
        return {"bookmarked": []}

    from src.collections.db import get_bookmarks
    bookmarks = get_bookmarks(user_id, get_db_path())
    bookmarked_ids = {b["repo_id"] for b in bookmarks}
    return {"bookmarked": [rid for rid in ids if rid in bookmarked_ids]}


@router.get("")
def list_bookmarks_endpoint(request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import get_bookmarks

    payload = require_auth(request)
    bms = get_bookmarks(payload["sub"], get_db_path())
    return {"bookmarks": bms, "total": len(bms)}
