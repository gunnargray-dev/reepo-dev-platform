"""Reepo comments — threaded comments on repos."""
from __future__ import annotations

import re

from src.db import _connect, DEFAULT_DB_PATH

MIN_COMMENT_LENGTH = 1
MAX_COMMENT_LENGTH = 10_000


def sanitize_comment_body(body: str) -> str:
    """Validate and sanitize a comment body.

    Strips HTML tags, enforces length limits, and rejects empty content.
    Returns the sanitized body string.
    Raises ValueError if the body is invalid.
    """
    if not isinstance(body, str):
        raise ValueError("Comment body must be a string")
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]*>", "", body)
    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()
    if len(cleaned) < MIN_COMMENT_LENGTH:
        raise ValueError("Comment body must not be empty")
    if len(cleaned) > MAX_COMMENT_LENGTH:
        raise ValueError(
            f"Comment body must not exceed {MAX_COMMENT_LENGTH} characters"
        )
    return cleaned


def add_comment(
    user_id: int,
    repo_id: int,
    body: str,
    parent_id: int | None = None,
    path: str = DEFAULT_DB_PATH,
) -> int:
    """Add a comment on a repo. Returns the comment id."""
    body = sanitize_comment_body(body)
    conn = _connect(path)
    cur = conn.execute(
        "INSERT INTO comments (user_id, repo_id, body, parent_id) VALUES (?, ?, ?, ?)",
        (user_id, repo_id, body, parent_id),
    )
    comment_id = cur.lastrowid
    conn.commit()
    conn.close()
    return comment_id


def get_comments(repo_id: int, limit: int = 50, path: str = DEFAULT_DB_PATH) -> list[dict]:
    """Get threaded comments for a repo. Top-level comments with nested replies."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM comments WHERE repo_id = ? ORDER BY created_at ASC LIMIT ?",
        (repo_id, limit),
    ).fetchall()
    conn.close()

    all_comments = [dict(r) for r in rows]
    top_level = []
    by_id: dict[int, dict] = {}
    for c in all_comments:
        c["replies"] = []
        by_id[c["id"]] = c

    for c in all_comments:
        if c["parent_id"] and c["parent_id"] in by_id:
            by_id[c["parent_id"]]["replies"].append(c)
        else:
            top_level.append(c)

    return top_level


def update_comment(comment_id: int, user_id: int, body: str, path: str = DEFAULT_DB_PATH) -> bool:
    """Update a comment. Only the owner can update. Returns True if updated."""
    body = sanitize_comment_body(body)
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE comments SET body = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ? AND user_id = ?",
        (body, comment_id, user_id),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def delete_comment(comment_id: int, user_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Delete a comment. Only the owner can delete. Returns True if deleted."""
    conn = _connect(path)
    cur = conn.execute(
        "DELETE FROM comments WHERE id = ? AND user_id = ?",
        (comment_id, user_id),
    )
    removed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def flag_comment(comment_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Flag a comment for moderation. Returns True if flagged."""
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE comments SET is_flagged = 1 WHERE id = ?", (comment_id,)
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def get_flagged_comments(path: str = DEFAULT_DB_PATH) -> list[dict]:
    """Get all flagged comments for admin review."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM comments WHERE is_flagged = 1 ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
