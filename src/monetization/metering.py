"""Reepo API metering — track usage and enforce rate limits per API key."""
from __future__ import annotations

from datetime import datetime, timezone

from src.db import _connect, DEFAULT_DB_PATH
from src.monetization.gates import FREE_API_LIMIT, PRO_API_LIMIT


def track_api_usage(
    api_key: str, endpoint: str, path: str = DEFAULT_DB_PATH
) -> None:
    """Record an API request."""
    conn = _connect(path)
    conn.execute(
        "INSERT INTO api_usage (api_key, endpoint) VALUES (?, ?)",
        (api_key, endpoint),
    )
    conn.commit()
    conn.close()


def get_requests_today(api_key: str, path: str = DEFAULT_DB_PATH) -> int:
    """Get the number of requests made today by an API key."""
    conn = _connect(path)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM api_usage "
        "WHERE api_key = ? AND timestamp >= ?",
        (api_key, today),
    ).fetchone()
    conn.close()
    return row["cnt"]


def check_api_limit(
    api_key: str, is_pro: bool = False, path: str = DEFAULT_DB_PATH
) -> bool:
    """Check if the API key is within its daily limit. Returns False if over limit."""
    limit = PRO_API_LIMIT if is_pro else FREE_API_LIMIT
    count = get_requests_today(api_key, path)
    return count < limit


def get_usage_stats(
    api_key: str, is_pro: bool = False, path: str = DEFAULT_DB_PATH
) -> dict:
    """Get usage statistics for an API key."""
    limit = PRO_API_LIMIT if is_pro else FREE_API_LIMIT
    requests_today = get_requests_today(api_key, path)
    remaining = max(0, limit - requests_today)
    # Reset at midnight UTC
    now = datetime.now(timezone.utc)
    reset_at = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if reset_at <= now:
        from datetime import timedelta
        reset_at = reset_at + timedelta(days=1)

    return {
        "requests_today": requests_today,
        "limit": limit,
        "remaining": remaining,
        "reset_at": reset_at.isoformat(),
        "is_pro": is_pro,
    }
