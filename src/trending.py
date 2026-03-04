"""Reepo trending — track star velocity and compute trending repos."""
import sqlite3
from datetime import datetime, timezone

from src.db import _connect, _row_to_dict, DEFAULT_DB_PATH

STAR_SNAPSHOTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS star_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    stars INTEGER NOT NULL,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);
CREATE INDEX IF NOT EXISTS idx_star_snapshots_repo ON star_snapshots(repo_id);
CREATE INDEX IF NOT EXISTS idx_star_snapshots_recorded ON star_snapshots(recorded_at);
"""


def init_trending_tables(path: str = DEFAULT_DB_PATH) -> None:
    """Create star_snapshots table if it doesn't exist."""
    conn = _connect(path)
    conn.executescript(STAR_SNAPSHOTS_SCHEMA)
    conn.commit()
    conn.close()


def record_star_snapshot(path: str = DEFAULT_DB_PATH) -> int:
    """Snapshot current stars for all repos. Returns count of snapshots taken."""
    conn = _connect(path)
    conn.executescript(STAR_SNAPSHOTS_SCHEMA)
    rows = conn.execute("SELECT id, stars FROM repos").fetchall()
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for row in rows:
        conn.execute(
            "INSERT INTO star_snapshots (repo_id, stars, recorded_at) VALUES (?, ?, ?)",
            (row["id"], row["stars"], now),
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def compute_trending(
    path: str = DEFAULT_DB_PATH,
    days: int = 7,
) -> list[dict]:
    """Compute star delta and trending score for repos over a given period.

    Returns list of dicts with repo data plus: star_delta, velocity, trending_score
    """
    conn = _connect(path)
    conn.executescript(STAR_SNAPSHOTS_SCHEMA)

    query = """
    WITH period_stats AS (
        SELECT
            s.repo_id,
            MAX(s.stars) - MIN(s.stars) as star_delta,
            COUNT(DISTINCT DATE(s.recorded_at)) as days_with_data
        FROM star_snapshots s
        WHERE s.recorded_at >= datetime('now', ?)
        GROUP BY s.repo_id
        HAVING star_delta > 0
    )
    SELECT r.*, ps.star_delta, ps.days_with_data
    FROM repos r
    JOIN period_stats ps ON r.id = ps.repo_id
    ORDER BY ps.star_delta DESC
    """
    rows = conn.execute(query, (f"-{days} days",)).fetchall()
    conn.close()

    results = []
    for row in rows:
        repo = _row_to_dict(row)
        star_delta = row["star_delta"]
        days_with_data = max(row["days_with_data"], 1)
        velocity = star_delta / days_with_data
        stars = repo.get("stars", 1) or 1
        trending_score = round(velocity * 100 / max(stars ** 0.3, 1), 2)
        repo["star_delta"] = star_delta
        repo["velocity"] = round(velocity, 2)
        repo["trending_score"] = trending_score
        results.append(repo)

    results.sort(key=lambda x: x["trending_score"], reverse=True)
    return results


def get_trending(
    path: str = DEFAULT_DB_PATH,
    period: str = "week",
    limit: int = 20,
) -> list[dict]:
    """Get top trending repos for a time period.

    Period: "day" (1 day), "week" (7 days), "month" (30 days)
    """
    period_map = {"day": 1, "week": 7, "month": 30}
    days = period_map.get(period, 7)
    results = compute_trending(path, days=days)
    return results[:limit]


def get_new_repos(
    path: str = DEFAULT_DB_PATH,
    days: int = 7,
    limit: int = 20,
) -> list[dict]:
    """Get recently indexed repos."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM repos WHERE indexed_at >= datetime('now', ?) "
        "ORDER BY indexed_at DESC LIMIT ?",
        (f"-{days} days", limit),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]
