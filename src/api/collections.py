"""Reepo API — collections CRUD and collection repos."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/collections", tags=["collections"])


class CollectionCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    is_public: bool = True


class CollectionUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    is_public: bool | None = None


class AddRepoBody(BaseModel):
    repo_id: int


@router.post("")
def create_collection_endpoint(body: CollectionCreate, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import create_collection

    payload = require_auth(request)
    path = get_db_path()
    cid = create_collection(
        user_id=payload["sub"],
        name=body.name,
        slug=body.slug,
        path=path,
        description=body.description,
        is_public=body.is_public,
    )
    return {"id": cid, "name": body.name, "slug": body.slug}


@router.get("")
def list_collections_endpoint(request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import list_collections

    payload = require_auth(request)
    colls = list_collections(payload["sub"], get_db_path())
    return {"collections": colls, "total": len(colls)}


@router.get("/{collection_id}")
def get_collection_endpoint(collection_id: int, request: Request):
    from src.server import get_db_path
    from src.collections.db import get_collection

    coll = get_collection(collection_id, get_db_path())
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    return coll


@router.put("/{collection_id}")
def update_collection_endpoint(collection_id: int, body: CollectionUpdate, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import update_collection

    payload = require_auth(request)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    ok = update_collection(collection_id, payload["sub"], get_db_path(), **updates)
    if not ok:
        raise HTTPException(status_code=404, detail="Collection not found or not owned by you")
    return {"updated": True}


@router.delete("/{collection_id}")
def delete_collection_endpoint(collection_id: int, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import delete_collection

    payload = require_auth(request)
    ok = delete_collection(collection_id, payload["sub"], get_db_path())
    if not ok:
        raise HTTPException(status_code=404, detail="Collection not found or not owned by you")
    return {"deleted": True}


# --- Collection repos ---

@router.post("/{collection_id}/repos")
def add_repo_to_collection_endpoint(collection_id: int, body: AddRepoBody, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import add_repo_to_collection, get_collection

    payload = require_auth(request)
    path = get_db_path()
    coll = get_collection(collection_id, path)
    if not coll or coll["user_id"] != payload["sub"]:
        raise HTTPException(status_code=404, detail="Collection not found")
    ok = add_repo_to_collection(collection_id, body.repo_id, path)
    if not ok:
        raise HTTPException(status_code=409, detail="Repo already in collection")
    return {"added": True}


@router.get("/{collection_id}/repos")
def list_collection_repos_endpoint(collection_id: int):
    from src.server import get_db_path
    from src.collections.db import get_collection, get_collection_repos

    path = get_db_path()
    coll = get_collection(collection_id, path)
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    repos = get_collection_repos(collection_id, path)
    return {"repos": repos, "total": len(repos)}


@router.delete("/{collection_id}/repos/{repo_id}")
def remove_repo_from_collection_endpoint(collection_id: int, repo_id: int, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import remove_repo_from_collection, get_collection

    payload = require_auth(request)
    path = get_db_path()
    coll = get_collection(collection_id, path)
    if not coll or coll["user_id"] != payload["sub"]:
        raise HTTPException(status_code=404, detail="Collection not found")
    ok = remove_repo_from_collection(collection_id, repo_id, path)
    if not ok:
        raise HTTPException(status_code=404, detail="Repo not in collection")
    return {"removed": True}
