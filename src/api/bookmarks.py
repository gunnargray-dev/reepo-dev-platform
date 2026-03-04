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


@router.get("")
def list_bookmarks_endpoint(request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import get_bookmarks

    payload = require_auth(request)
    bms = get_bookmarks(payload["sub"], get_db_path())
    return {"bookmarks": bms, "total": len(bms)}
