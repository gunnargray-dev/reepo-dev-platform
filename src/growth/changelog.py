"""Reepo changelog — record and retrieve repo events and milestones."""
from __future__ import annotations

import json

from src.db import _connect, DEFAULT_DB_PATH

MILESTONE_THRESHOLDS = [100, 500, 1000, 5000, 10000]


def record_event(
    repo_id: int,
    event_type: str,
    title: str,
    description: str | None = None,
    data: dict | None = None,
    path: str = DEFAULT_DB_PATH,
) -> int:
    """Record a repo event. Returns the event id."""
    conn = _connect(path)
    data_json = json.dumps(data) if data else None
    cur = conn.execute(
        "INSERT INTO repo_events (repo_id, event_type, title, description, data) "
        "VALUES (?, ?, ?, ?, ?)",
        (repo_id, event_type, title, description, data_json),
    )
    event_id = cur.lastrowid
    conn.commit()
    conn.close()
    return event_id


def get_repo_changelog(
    repo_id: int, limit: int = 20, path: str = DEFAULT_DB_PATH
) -> list[dict]:
    """Get changelog events for a repo, newest first."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM repo_events WHERE repo_id = ? "
        "ORDER BY occurred_at DESC, id DESC LIMIT ?",
        (repo_id, limit),
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        if d.get("data") and isinstance(d["data"], str):
            try:
                d["data"] = json.loads(d["data"])
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(d)
    return results


def detect_milestones(
    repo_id: int, current_stars: int, prev_stars: int
) -> list[dict]:
    """Detect star milestones crossed between prev and current star count."""
    milestones = []
    for threshold in MILESTONE_THRESHOLDS:
        if prev_stars < threshold <= current_stars:
            milestones.append({
                "repo_id": repo_id,
                "event_type": "milestone",
                "title": f"Reached {threshold:,} stars",
                "data": {
                    "threshold": threshold,
                    "current_stars": current_stars,
                    "prev_stars": prev_stars,
                },
            })
    return milestones


def detect_score_changes(
    repo_id: int, new_score: int, old_score: int, threshold: int = 5
) -> list[dict]:
    """Detect significant score changes above the threshold."""
    changes = []
    diff = new_score - old_score
    if abs(diff) >= threshold:
        direction = "increased" if diff > 0 else "decreased"
        changes.append({
            "repo_id": repo_id,
            "event_type": "score_change",
            "title": f"Score {direction} by {abs(diff)} points",
            "data": {
                "new_score": new_score,
                "old_score": old_score,
                "diff": diff,
            },
        })
    return changes
