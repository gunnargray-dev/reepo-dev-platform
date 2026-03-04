"""Reepo analytics pipeline — page views, search queries, conversion funnel."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from src.db import _connect, DEFAULT_DB_PATH


ANALYTICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS page_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    referrer TEXT,
    user_agent TEXT,
    ip_hash TEXT,
    user_id INTEGER,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    filters TEXT DEFAULT '{}',
    results_count INTEGER DEFAULT 0,
    user_id INTEGER,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_page_views_path ON page_views(path);
CREATE INDEX IF NOT EXISTS idx_page_views_recorded ON page_views(recorded_at);
CREATE INDEX IF NOT EXISTS idx_page_views_ip ON page_views(ip_hash);
CREATE INDEX IF NOT EXISTS idx_search_queries_recorded ON search_queries(recorded_at);
"""


def init_analytics_db(path: str = DEFAULT_DB_PATH) -> None:
    """Create analytics tables."""
    conn = _connect(path)
    conn.executescript(ANALYTICS_SCHEMA)
    conn.commit()
    conn.close()


def hash_ip(ip: str) -> str:
    """One-way hash an IP address for privacy."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def record_page_view(
    path: str,
    referrer: str = "",
    user_agent: str = "",
    ip: str = "",
    user_id: int | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    """Record a page view."""
    conn = _connect(db_path)
    conn.execute(
        "INSERT INTO page_views (path, referrer, user_agent, ip_hash, user_id) VALUES (?, ?, ?, ?, ?)",
        (path, referrer, user_agent, hash_ip(ip) if ip else "", user_id),
    )
    conn.commit()
    conn.close()


def record_search_query(
    query: str,
    filters: str = "{}",
    results_count: int = 0,
    user_id: int | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    """Record a search query."""
    conn = _connect(db_path)
    conn.execute(
        "INSERT INTO search_queries (query, filters, results_count, user_id) VALUES (?, ?, ?, ?)",
        (query, filters, results_count, user_id),
    )
    conn.commit()
    conn.close()


def get_analytics_summary(db_path: str = DEFAULT_DB_PATH, days: int = 30) -> dict:
    """Get analytics summary for the last N days."""
    conn = _connect(db_path)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Total views
    total_views = conn.execute(
        "SELECT COUNT(*) as cnt FROM page_views WHERE recorded_at >= ?", (cutoff,)
    ).fetchone()["cnt"]

    # Unique visitors (by ip_hash)
    unique_visitors = conn.execute(
        "SELECT COUNT(DISTINCT ip_hash) as cnt FROM page_views WHERE recorded_at >= ? AND ip_hash != ''",
        (cutoff,),
    ).fetchone()["cnt"]

    # Top pages
    top_pages = [
        dict(r) for r in conn.execute(
            "SELECT path, COUNT(*) as views FROM page_views "
            "WHERE recorded_at >= ? GROUP BY path ORDER BY views DESC LIMIT 20",
            (cutoff,),
        ).fetchall()
    ]

    # Top search queries
    top_search_queries = [
        dict(r) for r in conn.execute(
            "SELECT query, COUNT(*) as count, AVG(results_count) as avg_results "
            "FROM search_queries WHERE recorded_at >= ? "
            "GROUP BY query ORDER BY count DESC LIMIT 20",
            (cutoff,),
        ).fetchall()
    ]

    # Top repos viewed (from page_views matching /api/repos/*)
    top_repos_viewed = [
        dict(r) for r in conn.execute(
            "SELECT path, COUNT(*) as views FROM page_views "
            "WHERE recorded_at >= ? AND path LIKE '/api/repos/%' "
            "GROUP BY path ORDER BY views DESC LIMIT 10",
            (cutoff,),
        ).fetchall()
    ]

    # Conversion funnel
    visits = total_views
    searches = conn.execute(
        "SELECT COUNT(*) as cnt FROM search_queries WHERE recorded_at >= ?", (cutoff,)
    ).fetchone()["cnt"]
    repo_views = conn.execute(
        "SELECT COUNT(*) as cnt FROM page_views "
        "WHERE recorded_at >= ? AND path LIKE '/api/repos/%/%'",
        (cutoff,),
    ).fetchone()["cnt"]

    # Check for subscriptions table
    saves = 0
    signups = 0
    pro_upgrades = 0
    try:
        pro_upgrades = conn.execute(
            "SELECT COUNT(*) as cnt FROM subscriptions WHERE created_at >= ? AND plan != 'free'",
            (cutoff,),
        ).fetchone()["cnt"]
    except Exception:
        pass

    conn.close()

    return {
        "total_views": total_views,
        "unique_visitors": unique_visitors,
        "top_pages": top_pages,
        "top_search_queries": top_search_queries,
        "top_repos_viewed": top_repos_viewed,
        "conversion_funnel": {
            "visits": visits,
            "searches": searches,
            "views": repo_views,
            "saves": saves,
            "signups": signups,
            "pro_upgrades": pro_upgrades,
        },
        "period_days": days,
    }
