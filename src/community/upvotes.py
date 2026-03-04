"""Reepo upvotes — toggle upvotes on Built With projects."""
from __future__ import annotations

from src.db import _connect, DEFAULT_DB_PATH


def toggle_upvote(user_id: int, built_with_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Toggle an upvote. Returns True if upvoted, False if removed."""
    conn = _connect(path)
    existing = conn.execute(
        "SELECT id FROM upvotes WHERE user_id = ? AND built_with_id = ?",
        (user_id, built_with_id),
    ).fetchone()
    if existing:
        conn.execute(
            "DELETE FROM upvotes WHERE user_id = ? AND built_with_id = ?",
            (user_id, built_with_id),
        )
        conn.execute(
            "UPDATE built_with SET upvote_count = MAX(0, upvote_count - 1) WHERE id = ?",
            (built_with_id,),
        )
        conn.commit()
        conn.close()
        return False
    else:
        conn.execute(
            "INSERT INTO upvotes (user_id, built_with_id) VALUES (?, ?)",
            (user_id, built_with_id),
        )
        conn.execute(
            "UPDATE built_with SET upvote_count = upvote_count + 1 WHERE id = ?",
            (built_with_id,),
        )
        conn.commit()
        conn.close()
        return True


def get_upvote_count(built_with_id: int, path: str = DEFAULT_DB_PATH) -> int:
    """Get the upvote count for a Built With project."""
    conn = _connect(path)
    row = conn.execute(
        "SELECT upvote_count FROM built_with WHERE id = ?", (built_with_id,)
    ).fetchone()
    conn.close()
    return row["upvote_count"] if row else 0


def has_upvoted(user_id: int, built_with_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Check if a user has upvoted a project."""
    conn = _connect(path)
    row = conn.execute(
        "SELECT id FROM upvotes WHERE user_id = ? AND built_with_id = ?",
        (user_id, built_with_id),
    ).fetchone()
    conn.close()
    return row is not None
