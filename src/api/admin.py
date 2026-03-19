"""Reepo API — admin dashboard, moderation, and content management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class FeaturedRepoRequest(BaseModel):
    repo_id: int
    display_order: int = 0


@router.get("/api/admin/stats")
def api_admin_stats():
    from src.server import get_db_path
    from src.community.admin import get_admin_stats

    return get_admin_stats(path=get_db_path())


@router.get("/api/admin/moderation")
def api_moderation_queue():
    from src.server import get_db_path
    from src.community.admin import get_moderation_queue

    return get_moderation_queue(path=get_db_path())


@router.post("/api/admin/built-with/{project_id}/approve")
def api_approve_built_with(project_id: int):
    from src.server import get_db_path
    from src.community.built_with import approve_project

    if not approve_project(project_id, path=get_db_path()):
        raise HTTPException(status_code=404, detail="Project not found or not pending")
    return {"status": "approved"}


@router.post("/api/admin/built-with/{project_id}/reject")
def api_reject_built_with(project_id: int):
    from src.server import get_db_path
    from src.community.built_with import reject_project

    if not reject_project(project_id, path=get_db_path()):
        raise HTTPException(status_code=404, detail="Project not found or not pending")
    return {"status": "rejected"}


@router.post("/api/admin/submissions/{submission_id}/approve")
def api_approve_submission(submission_id: int):
    from src.server import get_db_path
    from src.community.submissions import approve_submission

    if not approve_submission(submission_id, path=get_db_path()):
        raise HTTPException(status_code=404, detail="Submission not found or not pending")
    return {"status": "approved"}


@router.post("/api/admin/submissions/{submission_id}/reject")
def api_reject_submission(submission_id: int):
    from src.server import get_db_path
    from src.community.submissions import reject_submission

    if not reject_submission(submission_id, path=get_db_path()):
        raise HTTPException(status_code=404, detail="Submission not found or not pending")
    return {"status": "rejected"}


@router.post("/api/admin/comments/{comment_id}/remove")
def api_remove_comment(comment_id: int):
    from src.server import get_db_path
    from src.db import _connect

    conn = _connect(get_db_path())
    cur = conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    removed = cur.rowcount > 0
    conn.commit()
    conn.close()
    if not removed:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"status": "removed"}


@router.get("/api/featured")
def api_get_featured():
    from src.server import get_db_path
    from src.db import get_featured_repos

    return {"repos": get_featured_repos(path=get_db_path())}


@router.post("/api/admin/featured")
def api_add_featured(req: FeaturedRepoRequest):
    from src.server import get_db_path
    from src.db import add_featured_repo

    if not add_featured_repo(req.repo_id, req.display_order, path=get_db_path()):
        raise HTTPException(status_code=409, detail="Repo already featured or not found")
    return {"status": "added"}


@router.delete("/api/admin/featured/{repo_id}")
def api_remove_featured(repo_id: int):
    from src.server import get_db_path
    from src.db import remove_featured_repo

    if not remove_featured_repo(repo_id, path=get_db_path()):
        raise HTTPException(status_code=404, detail="Repo not in featured list")
    return {"status": "removed"}
