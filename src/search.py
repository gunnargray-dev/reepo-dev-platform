"""Reepo full-text search — FTS5-based search with filters and pagination."""
import math
import sqlite3
from pathlib import Path

from src.db import _connect, _row_to_dict, DEFAULT_DB_PATH


def init_fts(path: str = DEFAULT_DB_PATH) -> None:
    """Create FTS5 virtual table and populate from repos table."""
    conn = _connect(path)
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS repos_fts USING fts5("
        "full_name, description, readme_excerpt, topics_text, "
        "content=''"
        ")"
    )
    conn.execute("DELETE FROM repos_fts")
    conn.execute(
        "INSERT INTO repos_fts(rowid, full_name, description, readme_excerpt, topics_text) "
        "SELECT id, full_name, COALESCE(description, ''), COALESCE(readme_excerpt, ''), "
        "REPLACE(REPLACE(COALESCE(topics, '[]'), '[', ''), ']', '') FROM repos"
    )
    conn.commit()
    conn.close()


def rebuild_fts(path: str = DEFAULT_DB_PATH) -> None:
    """Drop and rebuild FTS index."""
    conn = _connect(path)
    conn.execute("DROP TABLE IF EXISTS repos_fts")
    conn.close()
    init_fts(path)


def search(
    path: str = DEFAULT_DB_PATH,
    query: str = "",
    category: str | None = None,
    language: str | None = None,
    min_score: int = 0,
    sort: str = "relevance",
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """Search repos using FTS5 with filters, sorting, and pagination.

    Returns: {"results": [...], "total": int, "page": int, "per_page": int, "pages": int}
    """
    conn = _connect(path)

    _ensure_fts_exists(conn)

    has_query = bool(query and query.strip())
    clauses: list[str] = []
    params: list = []

    if has_query:
        fts_query = _sanitize_fts_query(query)
        clauses.append("repos.id IN (SELECT rowid FROM repos_fts WHERE repos_fts MATCH ?)")
        params.append(fts_query)

    if category:
        clauses.append("repos.category_primary = ?")
        params.append(category)
    if language:
        clauses.append("repos.language = ?")
        params.append(language)
    if min_score > 0:
        clauses.append("repos.reepo_score >= ?")
        params.append(min_score)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    count_sql = f"SELECT COUNT(*) as cnt FROM repos {where}"
    total = conn.execute(count_sql, params).fetchone()["cnt"]

    sort_map = {
        "stars": "repos.stars DESC",
        "score": "repos.reepo_score DESC",
        "newest": "repos.pushed_at DESC",
    }
    if has_query and sort == "relevance":
        order_clause = (
            "(SELECT rank FROM repos_fts WHERE repos_fts.rowid = repos.id AND repos_fts MATCH ?) ASC"
        )
        order_params = [fts_query]
    else:
        order_clause = sort_map.get(sort, "repos.stars DESC")
        order_params = []

    offset = (page - 1) * per_page
    data_sql = f"SELECT repos.* FROM repos {where} ORDER BY {order_clause} LIMIT ? OFFSET ?"
    data_params = params + order_params + [per_page, offset]
    rows = conn.execute(data_sql, data_params).fetchall()

    results = []
    for row in rows:
        repo = _row_to_dict(row)
        if has_query:
            snippet = _get_snippet(conn, fts_query, row["id"])
            if snippet:
                repo["snippet"] = snippet
        results.append(repo)

    conn.close()

    pages = max(1, math.ceil(total / per_page))
    return {
        "results": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def _ensure_fts_exists(conn: sqlite3.Connection) -> None:
    """Check if FTS table exists; create it if not."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='repos_fts'"
    ).fetchone()
    if not row:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS repos_fts USING fts5("
            "full_name, description, readme_excerpt, topics_text, "
            "content=''"
            ")"
        )
        conn.execute(
            "INSERT INTO repos_fts(rowid, full_name, description, readme_excerpt, topics_text) "
            "SELECT id, full_name, COALESCE(description, ''), COALESCE(readme_excerpt, ''), "
            "REPLACE(REPLACE(COALESCE(topics, '[]'), '[', ''), ']', '') FROM repos"
        )
        conn.commit()


def _sanitize_fts_query(query: str) -> str:
    """Sanitize user input for FTS5 MATCH safety."""
    cleaned = query.strip()
    if not cleaned:
        return '""'
    special = set('(){}[]^~*:')
    safe_tokens = []
    for token in cleaned.split():
        sanitized = "".join(c for c in token if c not in special)
        if sanitized:
            safe_tokens.append(f'"{sanitized}"')
    return " OR ".join(safe_tokens) if safe_tokens else '""'


def _get_snippet(conn: sqlite3.Connection, fts_query: str, repo_id: int) -> str | None:
    """Get highlighted snippet for a search result."""
    try:
        row = conn.execute(
            "SELECT highlight(repos_fts, 1, '<b>', '</b>') as snippet "
            "FROM repos_fts WHERE repos_fts MATCH ? AND rowid = ?",
            (fts_query, repo_id),
        ).fetchone()
        return row["snippet"] if row else None
    except sqlite3.OperationalError:
        return None
