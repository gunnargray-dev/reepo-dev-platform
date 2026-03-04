"""Reepo API — API key management."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/keys", tags=["api_keys"])


class KeyCreate(BaseModel):
    name: str
    daily_limit: int = 100


@router.post("")
def create_key_endpoint(body: KeyCreate, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.auth.db import create_api_key

    payload = require_auth(request)
    result = create_api_key(payload["sub"], body.name, get_db_path(), daily_limit=body.daily_limit)
    return result


@router.get("")
def list_keys_endpoint(request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.auth.db import get_api_keys_for_user

    payload = require_auth(request)
    keys = get_api_keys_for_user(payload["sub"], get_db_path())
    return {"keys": keys, "total": len(keys)}


@router.delete("/{key_id}")
def delete_key_endpoint(key_id: int, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.auth.db import delete_api_key

    payload = require_auth(request)
    ok = delete_api_key(key_id, payload["sub"], get_db_path())
    if not ok:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"deleted": True}
