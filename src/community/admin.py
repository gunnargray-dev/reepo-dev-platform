"""Reepo admin dashboard — stats and moderation queue."""
from __future__ import annotations

from src.db import _connect, DEFAULT_DB_PATH


def get_admin_stats(path: str = DEFAULT_DB_PATH) -> dict:
    """Get admin dashboard stats."""
    conn = _connect(path)
    total_repos = conn.execute("SELECT COUNT(*) as cnt FROM repos").fetchone()["cnt"]
    pending_submissions = conn.execute(
        "SELECT COUNT(*) as cnt FROM repo_submissions WHERE status = 'pending'"
    ).fetchone()["cnt"]
    flagged_comments = conn.execute(
        "SELECT COUNT(*) as cnt FROM comments WHERE is_flagged = 1"
    ).fetchone()["cnt"]
    pending_built_with = conn.execute(
        "SELECT COUNT(*) as cnt FROM built_with WHERE status = 'pending'"
    ).fetchone()["cnt"]
    total_comments = conn.execute(
        "SELECT COUNT(*) as cnt FROM comments"
    ).fetchone()["cnt"]
    total_built_with = conn.execute(
        "SELECT COUNT(*) as cnt FROM built_with"
    ).fetchone()["cnt"]
    conn.close()
    return {
        "total_repos": total_repos,
        "total_comments": total_comments,
        "total_built_with": total_built_with,
        "pending_submissions": pending_submissions,
        "flagged_comments": flagged_comments,
        "pending_built_with": pending_built_with,
    }


def get_moderation_queue(path: str = DEFAULT_DB_PATH) -> dict:
    """Get items needing moderation: pending Built With, flagged comments, pending submissions."""
    conn = _connect(path)

    pending_projects = conn.execute(
        "SELECT * FROM built_with WHERE status = 'pending' ORDER BY created_at ASC"
    ).fetchall()
    flagged = conn.execute(
        "SELECT * FROM comments WHERE is_flagged = 1 ORDER BY created_at DESC"
    ).fetchall()
    pending_subs = conn.execute(
        "SELECT * FROM repo_submissions WHERE status = 'pending' ORDER BY created_at ASC"
    ).fetchall()

    conn.close()
    return {
        "pending_built_with": [dict(r) for r in pending_projects],
        "flagged_comments": [dict(r) for r in flagged],
        "pending_submissions": [dict(r) for r in pending_subs],
    }


def remove_comment(comment_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Admin: remove a comment entirely. Returns True if deleted."""
    conn = _connect(path)
    cur = conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    removed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return removed
