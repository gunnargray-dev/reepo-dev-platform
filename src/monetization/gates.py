"""Reepo Pro feature gates — check pro status and enforce feature limits."""
from __future__ import annotations

from fastapi import HTTPException

from src.monetization.stripe_billing import get_subscription_status
from src.db import DEFAULT_DB_PATH

FREE_COLLECTION_LIMIT = 3
FREE_API_LIMIT = 100
PRO_API_LIMIT = 10000


def is_pro(user_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Check if a user has an active pro subscription."""
    status = get_subscription_status(user_id, path)
    return status.get("is_pro", False)


def require_pro(user_id: int | None, path: str = DEFAULT_DB_PATH) -> None:
    """Raise 403 if user is not pro. Use as a guard in route handlers."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not is_pro(user_id, path):
        raise HTTPException(
            status_code=403,
            detail="Pro subscription required. Upgrade at /pricing",
        )


def get_collection_limit(user_id: int | None, path: str = DEFAULT_DB_PATH) -> int:
    """Return the collection limit for a user."""
    if user_id is not None and is_pro(user_id, path):
        return 999999  # Unlimited for pro
    return FREE_COLLECTION_LIMIT


def get_api_limit(user_id: int | None, path: str = DEFAULT_DB_PATH) -> int:
    """Return the daily API request limit for a user."""
    if user_id is not None and is_pro(user_id, path):
        return PRO_API_LIMIT
    return FREE_API_LIMIT
