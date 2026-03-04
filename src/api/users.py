"""Reepo API — user profile, follow/unfollow, notifications."""
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/users", tags=["users"])


class UserUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    email: str | None = None
    avatar_url: str | None = None


# --- /me routes MUST come before /{username} and /{user_id} routes ---

@router.get("/me")
def get_my_profile(request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.auth.db import get_user_by_id

    payload = require_auth(request)
    user = get_user_by_id(payload["sub"], get_db_path())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me")
def update_my_profile(body: UserUpdate, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.auth.db import update_user

    payload = require_auth(request)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    ok = update_user(payload["sub"], get_db_path(), **updates)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"updated": True}


@router.get("/me/notifications")
def get_notifications_endpoint(request: Request, unread_only: bool = Query(False)):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import get_notifications

    payload = require_auth(request)
    notifs = get_notifications(payload["sub"], get_db_path(), unread_only=unread_only)
    return {"notifications": notifs, "total": len(notifs)}


@router.post("/me/notifications/{notification_id}/read")
def mark_notification_read_endpoint(notification_id: int, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import mark_notification_read

    payload = require_auth(request)
    ok = mark_notification_read(notification_id, payload["sub"], get_db_path())
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"marked_read": True}


@router.post("/me/notifications/read-all")
def mark_all_notifications_read_endpoint(request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import mark_all_notifications_read

    payload = require_auth(request)
    count = mark_all_notifications_read(payload["sub"], get_db_path())
    return {"marked_read": count}


# --- Parameterized routes ---

@router.get("/{username}")
def get_user_profile(username: str):
    from src.server import get_db_path
    from src.auth.db import get_user_by_username

    user = get_user_by_username(username, get_db_path())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    safe = {k: v for k, v in user.items() if k not in ("email", "github_id")}
    return safe


@router.post("/{user_id}/follow")
def follow_user_endpoint(user_id: int, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import follow_user

    payload = require_auth(request)
    if payload["sub"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    ok = follow_user(payload["sub"], user_id, get_db_path())
    if not ok:
        raise HTTPException(status_code=409, detail="Already following")
    return {"following": True}


@router.delete("/{user_id}/follow")
def unfollow_user_endpoint(user_id: int, request: Request):
    from src.server import get_db_path
    from src.auth.middleware import require_auth
    from src.collections.db import unfollow_user

    payload = require_auth(request)
    ok = unfollow_user(payload["sub"], user_id, get_db_path())
    if not ok:
        raise HTTPException(status_code=404, detail="Not following this user")
    return {"unfollowed": True}


@router.get("/{user_id}/followers")
def get_followers_endpoint(user_id: int):
    from src.server import get_db_path
    from src.collections.db import get_followers

    followers = get_followers(user_id, get_db_path())
    return {"followers": followers, "total": len(followers)}


@router.get("/{user_id}/following")
def get_following_endpoint(user_id: int):
    from src.server import get_db_path
    from src.collections.db import get_following

    following = get_following(user_id, get_db_path())
    return {"following": following, "total": len(following)}
