"""Reepo repo submissions — community-driven repo discovery."""
from __future__ import annotations

import re

from src.db import _connect, DEFAULT_DB_PATH

_GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$"
)


def submit_repo(
    user_id: int, github_url: str, path: str = DEFAULT_DB_PATH
) -> dict:
    """Submit a repo for inclusion. Validates URL and checks for duplicates."""
    github_url = github_url.strip().rstrip("/")
    if not _GITHUB_URL_RE.match(github_url):
        return {"ok": False, "error": "Invalid GitHub URL format"}

    conn = _connect(path)

    # Check if already submitted
    existing = conn.execute(
        "SELECT id, status FROM repo_submissions WHERE github_url = ?",
        (github_url,),
    ).fetchone()
    if existing:
        conn.close()
        return {
            "ok": False,
            "error": f"Already submitted (status: {existing['status']})",
            "submission_id": existing["id"],
        }

    # Check if already indexed
    parts = github_url.rstrip("/").split("/")
    owner, name = parts[-2], parts[-1]
    indexed = conn.execute(
        "SELECT id FROM repos WHERE owner = ? AND name = ?", (owner, name)
    ).fetchone()
    if indexed:
        conn.close()
        return {"ok": False, "error": "Repo is already indexed"}

    cur = conn.execute(
        "INSERT INTO repo_submissions (user_id, github_url) VALUES (?, ?)",
        (user_id, github_url),
    )
    submission_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"ok": True, "submission_id": submission_id}


def list_pending_submissions(path: str = DEFAULT_DB_PATH) -> list[dict]:
    """List all pending repo submissions."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM repo_submissions WHERE status = 'pending' "
        "ORDER BY created_at ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def approve_submission(submission_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Approve a pending submission. Returns True if status changed."""
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE repo_submissions SET status = 'approved', "
        "reviewed_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'pending'",
        (submission_id,),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def reject_submission(submission_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Reject a pending submission. Returns True if status changed."""
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE repo_submissions SET status = 'rejected', "
        "reviewed_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'pending'",
        (submission_id,),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed
