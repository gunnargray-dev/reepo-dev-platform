"""Reepo newsletter — subscriber management and digest generation."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from src.db import _connect, DEFAULT_DB_PATH


def subscribe(
    email: str, user_id: int | None = None, path: str = DEFAULT_DB_PATH
) -> bool:
    """Subscribe an email to the newsletter. Returns True if new subscriber."""
    if not _is_valid_email(email):
        return False
    conn = _connect(path)
    try:
        conn.execute(
            "INSERT INTO newsletter_subscribers (email, user_id, confirmed) VALUES (?, ?, 1)",
            (email, user_id),
        )
        conn.commit()
        result = True
    except Exception:
        result = False
    conn.close()
    return result


def unsubscribe(email: str, path: str = DEFAULT_DB_PATH) -> bool:
    """Unsubscribe an email. Returns True if was subscribed."""
    conn = _connect(path)
    cur = conn.execute(
        "DELETE FROM newsletter_subscribers WHERE email = ?", (email,)
    )
    removed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def get_subscriber_count(path: str = DEFAULT_DB_PATH) -> int:
    """Get the total number of confirmed subscribers."""
    conn = _connect(path)
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM newsletter_subscribers WHERE confirmed = 1"
    ).fetchone()
    conn.close()
    return row["cnt"]


def build_weekly_digest(path: str = DEFAULT_DB_PATH) -> dict:
    """Build newsletter content from the latest week's data."""
    conn = _connect(path)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    # Top trending repos this week
    trending = conn.execute(
        "SELECT r.full_name, r.description, r.stars, r.reepo_score, r.language "
        "FROM repos r ORDER BY r.stars DESC LIMIT 10"
    ).fetchall()

    # Newly indexed repos
    new_repos = conn.execute(
        "SELECT full_name, description, stars, language "
        "FROM repos WHERE indexed_at >= ? ORDER BY stars DESC LIMIT 5",
        (week_ago,),
    ).fetchall()

    # Newsletter sponsor for this week
    sponsor = conn.execute(
        "SELECT ns.*, s.name as sponsor_name "
        "FROM newsletter_sponsors ns "
        "JOIN sponsors s ON ns.sponsor_id = s.id "
        "ORDER BY ns.issue_date DESC LIMIT 1"
    ).fetchone()

    subscriber_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM newsletter_subscribers WHERE confirmed = 1"
    ).fetchone()["cnt"]

    conn.close()

    digest = {
        "title": f"Reepo Weekly — {datetime.now(timezone.utc).strftime('%B %d, %Y')}",
        "subscriber_count": subscriber_count,
        "trending": [dict(r) for r in trending],
        "new_repos": [dict(r) for r in new_repos],
        "sponsor": dict(sponsor) if sponsor else None,
    }
    return digest


def get_latest_newsletter(path: str = DEFAULT_DB_PATH) -> dict:
    """Get the latest newsletter digest content."""
    return build_weekly_digest(path)


def _is_valid_email(email: str) -> bool:
    """Basic email validation."""
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))
