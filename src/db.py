"""Reepo database layer — SQLite storage for repos, scores, and categories."""
import json
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = "data/reepo.db"

CATEGORIES = [
    ("frameworks", "Frameworks", "ML/AI frameworks and training libraries"),
    ("apis-sdks", "APIs & SDKs", "Client libraries and API wrappers for AI services"),
    ("agents", "Agents", "Autonomous agent frameworks and orchestration"),
    ("apps", "Apps", "End-user applications powered by AI"),
    ("tools-utilities", "Tools & Utilities", "Developer tools, CLIs, and utilities for AI workflows"),
    ("models", "Models", "Pre-trained models, model hubs, and model serving"),
    ("datasets", "Datasets", "Dataset loaders, benchmarks, and data processing"),
    ("infrastructure", "Infrastructure", "MLOps, deployment, and infrastructure tooling"),
    ("skills-plugins", "Skills & Plugins", "Plugins, extensions, and integrations for AI platforms"),
    ("libraries", "Libraries", "General-purpose AI/ML libraries and components"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    github_id INTEGER UNIQUE,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    description TEXT,
    url TEXT,
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    language TEXT,
    license TEXT,
    topics TEXT DEFAULT '[]',
    category_primary TEXT,
    categories_secondary TEXT DEFAULT '[]',
    reepo_score INTEGER,
    score_breakdown TEXT,
    readme_excerpt TEXT,
    last_analyzed_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    pushed_at TEXT,
    open_issues INTEGER DEFAULT 0,
    has_wiki INTEGER DEFAULT 0,
    homepage TEXT,
    indexed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS score_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    reepo_score INTEGER NOT NULL,
    score_breakdown TEXT,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    repo_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS featured_repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL UNIQUE,
    display_order INTEGER DEFAULT 0,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);

CREATE INDEX IF NOT EXISTS idx_repos_stars ON repos(stars DESC);
CREATE INDEX IF NOT EXISTS idx_repos_score ON repos(reepo_score DESC);
CREATE INDEX IF NOT EXISTS idx_repos_category ON repos(category_primary);
CREATE INDEX IF NOT EXISTS idx_repos_language ON repos(language);
CREATE INDEX IF NOT EXISTS idx_repos_updated ON repos(updated_at DESC);
"""


def _connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(path: str = DEFAULT_DB_PATH) -> None:
    conn = _connect(path)
    conn.executescript(SCHEMA)
    for slug, name, description in CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO categories (slug, name, description) VALUES (?, ?, ?)",
            (slug, name, description),
        )
    conn.commit()
    conn.close()


def insert_repo(repo: dict, path: str = DEFAULT_DB_PATH) -> int:
    conn = _connect(path)
    topics = json.dumps(repo.get("topics", []))
    categories_secondary = json.dumps(repo.get("categories_secondary", []))
    score_breakdown = json.dumps(repo.get("score_breakdown")) if repo.get("score_breakdown") else None
    cur = conn.execute(
        """INSERT INTO repos (
            github_id, owner, name, full_name, description, url, stars, forks,
            language, license, topics, category_primary, categories_secondary,
            reepo_score, score_breakdown, readme_excerpt, last_analyzed_at,
            created_at, updated_at, pushed_at, open_issues, has_wiki, homepage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            repo.get("github_id"),
            repo["owner"],
            repo["name"],
            repo["full_name"],
            repo.get("description"),
            repo.get("url"),
            repo.get("stars", 0),
            repo.get("forks", 0),
            repo.get("language"),
            repo.get("license"),
            topics,
            repo.get("category_primary"),
            categories_secondary,
            repo.get("reepo_score"),
            score_breakdown,
            repo.get("readme_excerpt"),
            repo.get("last_analyzed_at"),
            repo.get("created_at"),
            repo.get("updated_at"),
            repo.get("pushed_at"),
            repo.get("open_issues", 0),
            1 if repo.get("has_wiki") else 0,
            repo.get("homepage"),
        ),
    )
    repo_id = cur.lastrowid
    _update_category_count(conn, repo.get("category_primary"))
    conn.commit()
    conn.close()
    return repo_id


def update_repo(repo: dict, path: str = DEFAULT_DB_PATH) -> bool:
    conn = _connect(path)
    topics = json.dumps(repo.get("topics", []))
    categories_secondary = json.dumps(repo.get("categories_secondary", []))
    score_breakdown = json.dumps(repo.get("score_breakdown")) if repo.get("score_breakdown") else None
    cur = conn.execute(
        """UPDATE repos SET
            owner = ?, name = ?, full_name = ?, description = ?, url = ?,
            stars = ?, forks = ?, language = ?, license = ?, topics = ?,
            category_primary = ?, categories_secondary = ?,
            reepo_score = ?, score_breakdown = ?, readme_excerpt = ?,
            last_analyzed_at = ?, created_at = ?, updated_at = ?, pushed_at = ?,
            open_issues = ?, has_wiki = ?, homepage = ?
        WHERE github_id = ?""",
        (
            repo["owner"],
            repo["name"],
            repo["full_name"],
            repo.get("description"),
            repo.get("url"),
            repo.get("stars", 0),
            repo.get("forks", 0),
            repo.get("language"),
            repo.get("license"),
            topics,
            repo.get("category_primary"),
            categories_secondary,
            repo.get("reepo_score"),
            score_breakdown,
            repo.get("readme_excerpt"),
            repo.get("last_analyzed_at"),
            repo.get("created_at"),
            repo.get("updated_at"),
            repo.get("pushed_at"),
            repo.get("open_issues", 0),
            1 if repo.get("has_wiki") else 0,
            repo.get("homepage"),
            repo.get("github_id"),
        ),
    )
    changed = cur.rowcount > 0
    if changed:
        _recalculate_category_counts(conn)
    conn.commit()
    conn.close()
    return changed


def upsert_repo(repo: dict, path: str = DEFAULT_DB_PATH) -> int:
    conn = _connect(path)
    existing = conn.execute(
        "SELECT id FROM repos WHERE github_id = ?", (repo.get("github_id"),)
    ).fetchone()
    if not existing:
        existing = conn.execute(
            "SELECT id FROM repos WHERE full_name = ?", (repo.get("full_name"),)
        ).fetchone()
    conn.close()
    if existing:
        update_repo(repo, path)
        return existing["id"]
    return insert_repo(repo, path)


def get_repo(owner: str, name: str, path: str = DEFAULT_DB_PATH) -> dict | None:
    conn = _connect(path)
    row = conn.execute(
        "SELECT * FROM repos WHERE owner = ? AND name = ?", (owner, name)
    ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def get_repo_by_id(repo_id: int, path: str = DEFAULT_DB_PATH) -> dict | None:
    conn = _connect(path)
    row = conn.execute("SELECT * FROM repos WHERE id = ?", (repo_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def list_repos(
    path: str = DEFAULT_DB_PATH,
    category: str | None = None,
    language: str | None = None,
    min_score: int | None = None,
    sort_by: str = "stars",
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    conn = _connect(path)
    clauses = []
    params: list = []
    if category:
        clauses.append("category_primary = ?")
        params.append(category)
    if language:
        clauses.append("language = ?")
        params.append(language)
    if min_score is not None:
        clauses.append("reepo_score >= ?")
        params.append(min_score)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    allowed_sorts = {"stars", "reepo_score", "updated_at", "forks", "name"}
    if sort_by not in allowed_sorts:
        sort_by = "stars"
    order = f"{sort_by} DESC" if sort_by != "name" else "name ASC"
    query = f"SELECT * FROM repos {where} ORDER BY {order} LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def count_repos(path: str = DEFAULT_DB_PATH) -> int:
    conn = _connect(path)
    row = conn.execute("SELECT COUNT(*) as cnt FROM repos").fetchone()
    conn.close()
    return row["cnt"]


def get_unscored_repos(path: str = DEFAULT_DB_PATH) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM repos WHERE reepo_score IS NULL"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def record_score(
    repo_id: int, score: int, breakdown: dict, path: str = DEFAULT_DB_PATH
) -> None:
    conn = _connect(path)
    breakdown_json = json.dumps(breakdown)
    conn.execute(
        "INSERT INTO score_history (repo_id, reepo_score, score_breakdown) VALUES (?, ?, ?)",
        (repo_id, score, breakdown_json),
    )
    conn.execute(
        "UPDATE repos SET reepo_score = ?, score_breakdown = ?, last_analyzed_at = CURRENT_TIMESTAMP WHERE id = ?",
        (score, breakdown_json, repo_id),
    )
    conn.commit()
    conn.close()


def get_score_history(
    repo_id: int, path: str = DEFAULT_DB_PATH
) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM score_history WHERE repo_id = ? ORDER BY recorded_at DESC",
        (repo_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_categories(path: str = DEFAULT_DB_PATH) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM categories ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_repos_by_category(path: str = DEFAULT_DB_PATH) -> dict[str, int]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT category_primary, COUNT(*) as cnt FROM repos "
        "WHERE category_primary IS NOT NULL GROUP BY category_primary ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return {r["category_primary"]: r["cnt"] for r in rows}


def get_repos_by_language(path: str = DEFAULT_DB_PATH, limit: int = 10) -> dict[str, int]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT language, COUNT(*) as cnt FROM repos "
        "WHERE language IS NOT NULL GROUP BY language ORDER BY cnt DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return {r["language"]: r["cnt"] for r in rows}


def get_score_stats(path: str = DEFAULT_DB_PATH) -> dict:
    conn = _connect(path)
    row = conn.execute(
        "SELECT AVG(reepo_score) as avg_score, MIN(reepo_score) as min_score, "
        "MAX(reepo_score) as max_score FROM repos WHERE reepo_score IS NOT NULL"
    ).fetchone()
    dist = conn.execute(
        "SELECT "
        "SUM(CASE WHEN reepo_score >= 80 THEN 1 ELSE 0 END) as excellent, "
        "SUM(CASE WHEN reepo_score >= 60 AND reepo_score < 80 THEN 1 ELSE 0 END) as good, "
        "SUM(CASE WHEN reepo_score >= 40 AND reepo_score < 60 THEN 1 ELSE 0 END) as fair, "
        "SUM(CASE WHEN reepo_score < 40 THEN 1 ELSE 0 END) as poor "
        "FROM repos WHERE reepo_score IS NOT NULL"
    ).fetchone()
    conn.close()
    return {
        "avg_score": round(row["avg_score"]) if row["avg_score"] else 0,
        "min_score": row["min_score"] or 0,
        "max_score": row["max_score"] or 0,
        "distribution": {
            "excellent_80_plus": dist["excellent"] or 0,
            "good_60_79": dist["good"] or 0,
            "fair_40_59": dist["fair"] or 0,
            "poor_below_40": dist["poor"] or 0,
        },
    }


def get_featured_repos(path: str = DEFAULT_DB_PATH) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT r.* FROM repos r "
        "JOIN featured_repos f ON f.repo_id = r.id "
        "ORDER BY f.display_order ASC, f.added_at DESC"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def add_featured_repo(repo_id: int, display_order: int = 0, path: str = DEFAULT_DB_PATH) -> bool:
    conn = _connect(path)
    try:
        conn.execute(
            "INSERT INTO featured_repos (repo_id, display_order) VALUES (?, ?)",
            (repo_id, display_order),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_featured_repo(repo_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    conn = _connect(path)
    cur = conn.execute("DELETE FROM featured_repos WHERE repo_id = ?", (repo_id,))
    removed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for key in ("topics", "categories_secondary", "score_breakdown", "use_cases"):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def _update_category_count(conn: sqlite3.Connection, category: str | None) -> None:
    if category:
        conn.execute(
            "UPDATE categories SET repo_count = "
            "(SELECT COUNT(*) FROM repos WHERE category_primary = ?) "
            "WHERE slug = ?",
            (category, category),
        )


def _recalculate_category_counts(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE categories SET repo_count = "
        "(SELECT COUNT(*) FROM repos WHERE category_primary = categories.slug)"
    )
