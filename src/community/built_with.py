"""Reepo Built With — showcase projects built using indexed repos."""
from __future__ import annotations

import json

from src.db import _connect, DEFAULT_DB_PATH


def submit_project(
    user_id: int,
    title: str,
    description: str,
    url: str,
    repo_ids: list[int],
    screenshot_url: str | None = None,
    path: str = DEFAULT_DB_PATH,
) -> int:
    """Submit a new Built With project. Returns the project id."""
    conn = _connect(path)
    cur = conn.execute(
        "INSERT INTO built_with (user_id, title, description, url, screenshot_url) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, title, description, url, screenshot_url),
    )
    project_id = cur.lastrowid
    for repo_id in repo_ids:
        conn.execute(
            "INSERT INTO built_with_repos (built_with_id, repo_id) VALUES (?, ?)",
            (project_id, repo_id),
        )
    conn.commit()
    conn.close()
    return project_id


def get_project(project_id: int, path: str = DEFAULT_DB_PATH) -> dict | None:
    """Get a single project with its associated repo ids."""
    conn = _connect(path)
    row = conn.execute("SELECT * FROM built_with WHERE id = ?", (project_id,)).fetchone()
    if not row:
        conn.close()
        return None
    project = dict(row)
    repo_rows = conn.execute(
        "SELECT repo_id FROM built_with_repos WHERE built_with_id = ?", (project_id,)
    ).fetchall()
    project["repo_ids"] = [r["repo_id"] for r in repo_rows]
    conn.close()
    return project


def list_projects(
    status: str = "approved",
    sort: str = "upvotes",
    limit: int = 20,
    offset: int = 0,
    path: str = DEFAULT_DB_PATH,
) -> list[dict]:
    """List projects filtered by status, sorted by upvotes or date."""
    sort_map = {
        "upvotes": "upvote_count DESC",
        "newest": "created_at DESC",
    }
    order = sort_map.get(sort, "upvote_count DESC")
    conn = _connect(path)
    rows = conn.execute(
        f"SELECT * FROM built_with WHERE status = ? ORDER BY {order} LIMIT ? OFFSET ?",
        (status, limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_projects_for_repo(repo_id: int, path: str = DEFAULT_DB_PATH) -> list[dict]:
    """List approved Built With projects that use a specific repo."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT bw.* FROM built_with bw "
        "INNER JOIN built_with_repos bwr ON bwr.built_with_id = bw.id "
        "WHERE bwr.repo_id = ? AND bw.status = 'approved' "
        "ORDER BY bw.upvote_count DESC",
        (repo_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def approve_project(project_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Approve a pending project. Returns True if status changed."""
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE built_with SET status = 'approved', updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ? AND status = 'pending'",
        (project_id,),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def reject_project(project_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Reject a pending project. Returns True if status changed."""
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE built_with SET status = 'rejected', updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ? AND status = 'pending'",
        (project_id,),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed
