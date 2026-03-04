"""Reepo full-text search — FTS5-based search with filters and pagination."""
from __future__ import annotations

import math
import re
import sqlite3
import unicodedata

from src.db import _connect, _row_to_dict, DEFAULT_DB_PATH

# FTS5 reserved keywords that must not appear as bare tokens in MATCH queries
_FTS5_OPERATORS = {"AND", "OR", "NOT", "NEAR"}

# Max query length to prevent abuse
_MAX_QUERY_LENGTH = 500


def init_fts(path: str = DEFAULT_DB_PATH) -> None:
    """Create FTS5 virtual table and populate from repos table."""
    conn = _connect(path)
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS repos_fts USING fts5("
        "full_name, description, readme_excerpt, topics_text"
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

    Uses a single JOIN against repos_fts for rank and snippets instead of
    correlated subqueries, which is significantly faster on large tables.

    Returns: {"results": [...], "total": int, "page": int, "per_page": int, "pages": int}
    """
    conn = _connect(path)

    _ensure_fts_exists(conn)

    has_query = bool(query and query.strip())
    fts_query = ""
    filter_clauses: list[str] = []
    filter_params: list = []

    if has_query:
        fts_query = _sanitize_fts_query(query)

    if category:
        filter_clauses.append("repos.category_primary = ?")
        filter_params.append(category)
    if language:
        filter_clauses.append("repos.language = ?")
        filter_params.append(language)
    if min_score > 0:
        filter_clauses.append("repos.reepo_score >= ?")
        filter_params.append(min_score)

    # --- Count query ---
    if has_query:
        count_clauses = ["repos_fts MATCH ?"] + [
            c.replace("repos.", "") for c in filter_clauses
        ]
        # JOIN repos so we can filter on its columns
        count_sql = (
            "SELECT COUNT(*) AS cnt FROM repos "
            "INNER JOIN repos_fts ON repos_fts.rowid = repos.id "
            f"WHERE {' AND '.join(count_clauses)}"
        )
        count_params = [fts_query] + filter_params
    else:
        filter_where = f"WHERE {' AND '.join(filter_clauses)}" if filter_clauses else ""
        count_sql = f"SELECT COUNT(*) AS cnt FROM repos {filter_where}"
        count_params = filter_params

    total = conn.execute(count_sql, count_params).fetchone()["cnt"]

    sort_map = {
        "stars": "repos.stars DESC",
        "score": "repos.reepo_score DESC",
        "newest": "repos.pushed_at DESC",
    }

    offset = (page - 1) * per_page

    if has_query:
        # Single JOIN against repos_fts for MATCH, rank, and snippet in one pass.
        if sort == "relevance":
            order_clause = "repos_fts.rank ASC"
        else:
            order_clause = sort_map.get(sort, "repos.stars DESC")

        data_clauses = ["repos_fts MATCH ?"] + filter_clauses
        data_sql = (
            "SELECT repos.*, repos_fts.rank AS _fts_rank, "
            "snippet(repos_fts, -1, '<b>', '</b>', '...', 32) AS _snippet "
            "FROM repos "
            "INNER JOIN repos_fts ON repos_fts.rowid = repos.id "
            f"WHERE {' AND '.join(data_clauses)} "
            f"ORDER BY {order_clause} LIMIT ? OFFSET ?"
        )
        data_params = [fts_query] + filter_params + [per_page, offset]
        rows = conn.execute(data_sql, data_params).fetchall()

        results = []
        for row in rows:
            repo = _row_to_dict(row)
            snippet = row["_snippet"]
            if snippet:
                repo["snippet"] = snippet
            repo.pop("_fts_rank", None)
            repo.pop("_snippet", None)
            results.append(repo)
    else:
        order_clause = sort_map.get(sort, "repos.stars DESC")
        filter_where = f"WHERE {' AND '.join(filter_clauses)}" if filter_clauses else ""
        data_sql = f"SELECT repos.* FROM repos {filter_where} ORDER BY {order_clause} LIMIT ? OFFSET ?"
        data_params = filter_params + [per_page, offset]
        rows = conn.execute(data_sql, data_params).fetchall()
        results = [_row_to_dict(row) for row in rows]

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
            "full_name, description, readme_excerpt, topics_text"
            ")"
        )
        conn.execute(
            "INSERT INTO repos_fts(rowid, full_name, description, readme_excerpt, topics_text) "
            "SELECT id, full_name, COALESCE(description, ''), COALESCE(readme_excerpt, ''), "
            "REPLACE(REPLACE(COALESCE(topics, '[]'), '[', ''), ']', '') FROM repos"
        )
        conn.commit()


def _sanitize_fts_query(query: str) -> str:
    """Sanitize user input for FTS5 MATCH safety.

    Handles: unbalanced quotes, unicode normalization, FTS5 operator injection
    (AND/OR/NOT/NEAR), special characters, empty/whitespace input, and
    excessively long queries. Each token is double-quoted to prevent any
    FTS5 syntax interpretation.
    """
    cleaned = query.strip()
    if not cleaned:
        return '""'

    # Truncate overly long queries
    cleaned = cleaned[:_MAX_QUERY_LENGTH]

    # Normalize unicode (e.g. decomposed accents → composed form)
    cleaned = unicodedata.normalize("NFKC", cleaned)

    # Strip null bytes and other control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', "", cleaned)

    # Strip all double quotes to prevent injection into quoted phrases
    cleaned = cleaned.replace('"', "")

    # Remove FTS5-special characters: punctuation that has meaning in FTS5 syntax
    cleaned = re.sub(r'[(){}[\]^~*:+\-<>]', " ", cleaned)

    safe_tokens = []
    for token in cleaned.split():
        # Skip FTS5 operator keywords (AND, OR, NOT, NEAR)
        if token.upper() in _FTS5_OPERATORS:
            continue
        # Skip tokens that are only whitespace/empty after stripping
        if not token:
            continue
        # Quote each token to prevent FTS5 interpretation
        safe_tokens.append(f'"{token}"')

    return " OR ".join(safe_tokens) if safe_tokens else '""'
