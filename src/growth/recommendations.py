"""Reepo recommendations — personalized repo suggestions."""
from __future__ import annotations

from src.db import _connect, _row_to_dict, DEFAULT_DB_PATH


def get_recommendations_for_user(
    user_id: int, db_path: str = DEFAULT_DB_PATH, limit: int = 10
) -> list[dict]:
    """Get recommendations based on user's bookmarked repo categories/topics.

    Gracefully handles missing bookmark tables by returning [].
    """
    conn = _connect(db_path)

    # Check if bookmarks table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'"
    ).fetchone()
    if not table_check:
        conn.close()
        return []

    # Get user's bookmarked repo categories
    bookmarked = conn.execute(
        "SELECT DISTINCT r.category_primary FROM bookmarks b "
        "JOIN repos r ON b.repo_id = r.id WHERE b.user_id = ?",
        (user_id,),
    ).fetchall()

    if not bookmarked:
        # Fallback: return top-scored repos
        rows = conn.execute(
            "SELECT * FROM repos WHERE reepo_score IS NOT NULL "
            "ORDER BY reepo_score DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]

    categories = [r["category_primary"] for r in bookmarked if r["category_primary"]]
    if not categories:
        conn.close()
        return []

    placeholders = ",".join("?" * len(categories))

    # Get bookmarked repo IDs to exclude
    bookmarked_ids = conn.execute(
        "SELECT repo_id FROM bookmarks WHERE user_id = ?", (user_id,)
    ).fetchall()
    exclude_ids = {r["repo_id"] for r in bookmarked_ids}

    rows = conn.execute(
        f"SELECT * FROM repos WHERE category_primary IN ({placeholders}) "
        "ORDER BY reepo_score DESC NULLS LAST LIMIT ?",
        (*categories, limit + len(exclude_ids)),
    ).fetchall()

    results = []
    for r in rows:
        d = _row_to_dict(r)
        if d["id"] not in exclude_ids:
            results.append(d)
        if len(results) >= limit:
            break

    conn.close()
    return results


def get_collaborative_recommendations(
    user_id: int, db_path: str = DEFAULT_DB_PATH, limit: int = 10
) -> list[dict]:
    """Get recommendations based on what similar users bookmarked.

    Gracefully handles missing bookmark tables by returning [].
    """
    conn = _connect(db_path)

    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'"
    ).fetchone()
    if not table_check:
        conn.close()
        return []

    # Find repos bookmarked by users who share bookmarks with this user
    rows = conn.execute(
        "SELECT DISTINCT r.* FROM repos r "
        "JOIN bookmarks b2 ON b2.repo_id = r.id "
        "WHERE b2.user_id IN ("
        "  SELECT DISTINCT b3.user_id FROM bookmarks b3 "
        "  WHERE b3.repo_id IN (SELECT repo_id FROM bookmarks WHERE user_id = ?) "
        "  AND b3.user_id != ?"
        ") "
        "AND r.id NOT IN (SELECT repo_id FROM bookmarks WHERE user_id = ?) "
        "ORDER BY r.reepo_score DESC NULLS LAST LIMIT ?",
        (user_id, user_id, user_id, limit),
    ).fetchall()

    conn.close()
    return [_row_to_dict(r) for r in rows]
