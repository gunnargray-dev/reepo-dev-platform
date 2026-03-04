"""Reepo API — auth routes: GitHub OAuth, token refresh, logout, profile."""
import secrets

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/github")
def auth_github_redirect(state: str = Query(None)):
    from src.auth.github_oauth import get_auth_url
    url = get_auth_url(state=state)
    return {"auth_url": url}


@router.get("/github/callback")
def auth_github_callback(code: str = Query(...), state: str = Query(None)):
    from src.server import get_db_path
    from src.auth.github_oauth import exchange_code, get_github_user
    from src.auth.db import get_user_by_github_id, create_user, create_session
    from src.auth.jwt_auth import create_access_token, create_refresh_token

    try:
        token_data = exchange_code(code)
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {e}")

    access_tok = token_data.get("access_token")
    if not access_tok:
        raise HTTPException(status_code=400, detail="No access token returned")

    try:
        gh_user = get_github_user(access_tok)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch GitHub user: {e}")

    path = get_db_path()
    github_id = gh_user.get("id")
    user = get_user_by_github_id(github_id, path)

    if not user:
        user_id = create_user(
            username=gh_user.get("login", f"user_{github_id}"),
            path=path,
            github_id=github_id,
            email=gh_user.get("email"),
            display_name=gh_user.get("name"),
            avatar_url=gh_user.get("avatar_url"),
            bio=gh_user.get("bio"),
        )
    else:
        user_id = user["id"]

    jwt_access = create_access_token(user_id)
    jwt_refresh = create_refresh_token(user_id)

    from datetime import datetime, timezone, timedelta
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    create_session(user_id, jwt_access, jwt_refresh, expires, path)

    return {
        "access_token": jwt_access,
        "refresh_token": jwt_refresh,
        "token_type": "bearer",
        "user_id": user_id,
    }


@router.post("/refresh")
def auth_refresh(request: Request):
    from src.server import get_db_path
    from src.auth.jwt_auth import decode_token, create_access_token, create_refresh_token
    from src.auth.db import get_session_by_refresh, delete_session, create_session

    body_token = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        body_token = auth[7:]

    if not body_token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    try:
        payload = decode_token(body_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    path = get_db_path()
    session = get_session_by_refresh(body_token, path)
    if not session:
        raise HTTPException(status_code=401, detail="Session not found")

    # Rotate tokens
    delete_session(session["token"], path)
    user_id = payload["sub"]
    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)

    from datetime import datetime, timezone, timedelta
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    create_session(user_id, new_access, new_refresh, expires, path)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
def auth_logout(request: Request):
    from src.server import get_db_path
    from src.auth.db import delete_session

    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Token required")

    path = get_db_path()
    deleted = delete_session(token, path)
    return {"logged_out": deleted}


@router.get("/me")
def auth_me(request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.auth.db import get_user_by_id

    payload = require_auth(request)
    user = get_user_by_id(payload["sub"], get_db_path())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("github_id", None)
    return user
