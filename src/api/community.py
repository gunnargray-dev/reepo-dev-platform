"""Reepo API — community endpoints: Built With, comments, submissions, digest."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class SubmitProjectRequest(BaseModel):
    user_id: int
    title: str
    description: str
    url: str
    repo_ids: list[int] = []
    screenshot_url: str | None = None


class AddCommentRequest(BaseModel):
    user_id: int
    body: str
    parent_id: int | None = None


class SubmitRepoRequest(BaseModel):
    user_id: int
    github_url: str


# --- Built With ---

@router.post("/api/built-with")
def api_submit_project(req: SubmitProjectRequest):
    from src.server import get_db_path
    from src.community.built_with import submit_project
    project_id = submit_project(
        user_id=req.user_id,
        title=req.title,
        description=req.description,
        url=req.url,
        repo_ids=req.repo_ids,
        screenshot_url=req.screenshot_url,
        path=get_db_path(),
    )
    return {"id": project_id, "status": "pending"}


@router.get("/api/built-with")
def api_list_projects(sort: str = "upvotes", limit: int = 20, offset: int = 0):
    from src.server import get_db_path
    from src.community.built_with import list_projects
    return list_projects(sort=sort, limit=limit, offset=offset, path=get_db_path())


@router.get("/api/built-with/{project_id}")
def api_get_project(project_id: int):
    from src.server import get_db_path
    from src.community.built_with import get_project
    project = get_project(project_id, get_db_path())
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.post("/api/built-with/{project_id}/upvote")
def api_toggle_upvote(project_id: int, user_id: int):
    from src.server import get_db_path
    from src.community.upvotes import toggle_upvote
    upvoted = toggle_upvote(user_id, project_id, get_db_path())
    return {"upvoted": upvoted}


# --- Repo Built With ---

@router.get("/api/repos/{owner}/{name}/built-with")
def api_repo_built_with(owner: str, name: str):
    from src.server import get_db_path
    from src.db import get_repo
    from src.community.built_with import list_projects_for_repo
    repo = get_repo(owner, name, get_db_path())
    if not repo:
        raise HTTPException(404, "Repo not found")
    return list_projects_for_repo(repo["id"], get_db_path())


# --- Comments ---

@router.get("/api/repos/{owner}/{name}/comments")
def api_get_comments(owner: str, name: str, limit: int = 50):
    from src.server import get_db_path
    from src.db import get_repo
    from src.community.comments import get_comments
    repo = get_repo(owner, name, get_db_path())
    if not repo:
        raise HTTPException(404, "Repo not found")
    return get_comments(repo["id"], limit=limit, path=get_db_path())


@router.post("/api/repos/{owner}/{name}/comments")
def api_add_comment(owner: str, name: str, req: AddCommentRequest):
    from src.server import get_db_path
    from src.db import get_repo
    from src.community.comments import add_comment
    repo = get_repo(owner, name, get_db_path())
    if not repo:
        raise HTTPException(404, "Repo not found")
    comment_id = add_comment(
        user_id=req.user_id,
        repo_id=repo["id"],
        body=req.body,
        parent_id=req.parent_id,
        path=get_db_path(),
    )
    return {"id": comment_id}


# --- Submissions ---

@router.post("/api/submissions")
def api_submit_repo(req: SubmitRepoRequest):
    from src.server import get_db_path
    from src.community.submissions import submit_repo
    result = submit_repo(req.user_id, req.github_url, get_db_path())
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "Submission failed"))
    return {"id": result["submission_id"], "status": "pending"}


# --- Digest ---

@router.get("/api/digest/latest")
def api_latest_digest():
    from src.server import get_db_path
    from src.community.digest import get_latest_digest
    digest = get_latest_digest(get_db_path())
    if not digest:
        raise HTTPException(404, "No digest available")
    return digest
