"""Reepo collections database — collections, bookmarks, follows, notifications."""
import json
import sqlite3
from pathlib import Path

COLLECTIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS collection_repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(collection_id, repo_id),
    FOREIGN KEY (collection_id) REFERENCES collections(id),
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, repo_id)
);

CREATE TABLE IF NOT EXISTS follows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower_id INTEGER NOT NULL,
    following_id INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(follower_id, following_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT,
    is_read BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_collections_user ON collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collection_repos_coll ON collection_repos(collection_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
"""


def _connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_collections_db(path: str) -> None:
    conn = _connect(path)
    conn.executescript(COLLECTIONS_SCHEMA)
    conn.commit()
    conn.close()


# --- Collections ---

def create_collection(
    user_id: int, name: str, slug: str, path: str,
    description: str | None = None, is_public: bool = True,
) -> int:
    conn = _connect(path)
    cur = conn.execute(
        "INSERT INTO collections (user_id, name, slug, description, is_public) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, slug, description, 1 if is_public else 0),
    )
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def get_collection(collection_id: int, path: str) -> dict | None:
    conn = _connect(path)
    row = conn.execute("SELECT * FROM collections WHERE id = ?", (collection_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_collections(user_id: int, path: str) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM collections WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_collection(collection_id: int, user_id: int, path: str, **kwargs) -> bool:
    allowed = {"name", "slug", "description", "is_public"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return False
    if "is_public" in fields:
        fields["is_public"] = 1 if fields["is_public"] else 0
    sets = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [collection_id, user_id]
    conn = _connect(path)
    cur = conn.execute(
        f"UPDATE collections SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        vals,
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def delete_collection(collection_id: int, user_id: int, path: str) -> bool:
    conn = _connect(path)
    conn.execute("DELETE FROM collection_repos WHERE collection_id = ?", (collection_id,))
    cur = conn.execute(
        "DELETE FROM collections WHERE id = ? AND user_id = ?", (collection_id, user_id)
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


# --- Collection Repos ---

def add_repo_to_collection(collection_id: int, repo_id: int, path: str) -> bool:
    conn = _connect(path)
    try:
        conn.execute(
            "INSERT INTO collection_repos (collection_id, repo_id) VALUES (?, ?)",
            (collection_id, repo_id),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def remove_repo_from_collection(collection_id: int, repo_id: int, path: str) -> bool:
    conn = _connect(path)
    cur = conn.execute(
        "DELETE FROM collection_repos WHERE collection_id = ? AND repo_id = ?",
        (collection_id, repo_id),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def get_collection_repos(collection_id: int, path: str) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT cr.*, r.owner, r.name, r.full_name, r.description, r.stars, r.reepo_score "
        "FROM collection_repos cr "
        "LEFT JOIN repos r ON cr.repo_id = r.id "
        "WHERE cr.collection_id = ? ORDER BY cr.added_at DESC",
        (collection_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Bookmarks ---

def add_bookmark(user_id: int, repo_id: int, path: str) -> bool:
    conn = _connect(path)
    try:
        conn.execute(
            "INSERT INTO bookmarks (user_id, repo_id) VALUES (?, ?)",
            (user_id, repo_id),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def remove_bookmark(user_id: int, repo_id: int, path: str) -> bool:
    conn = _connect(path)
    cur = conn.execute(
        "DELETE FROM bookmarks WHERE user_id = ? AND repo_id = ?",
        (user_id, repo_id),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def get_bookmarks(user_id: int, path: str) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT b.*, r.owner, r.name, r.full_name, r.description, r.stars, r.reepo_score "
        "FROM bookmarks b "
        "LEFT JOIN repos r ON b.repo_id = r.id "
        "WHERE b.user_id = ? ORDER BY b.created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Follows ---

def follow_user(follower_id: int, following_id: int, path: str) -> bool:
    if follower_id == following_id:
        return False
    conn = _connect(path)
    try:
        conn.execute(
            "INSERT INTO follows (follower_id, following_id) VALUES (?, ?)",
            (follower_id, following_id),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def unfollow_user(follower_id: int, following_id: int, path: str) -> bool:
    conn = _connect(path)
    cur = conn.execute(
        "DELETE FROM follows WHERE follower_id = ? AND following_id = ?",
        (follower_id, following_id),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def get_followers(user_id: int, path: str) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT f.*, u.username, u.display_name, u.avatar_url "
        "FROM follows f "
        "LEFT JOIN users u ON f.follower_id = u.id "
        "WHERE f.following_id = ? ORDER BY f.created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_following(user_id: int, path: str) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT f.*, u.username, u.display_name, u.avatar_url "
        "FROM follows f "
        "LEFT JOIN users u ON f.following_id = u.id "
        "WHERE f.follower_id = ? ORDER BY f.created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Notifications ---

def create_notification(
    user_id: int, type_: str, message: str, path: str, data: dict | None = None,
) -> int:
    conn = _connect(path)
    data_json = json.dumps(data) if data else None
    cur = conn.execute(
        "INSERT INTO notifications (user_id, type, message, data) VALUES (?, ?, ?, ?)",
        (user_id, type_, message, data_json),
    )
    nid = cur.lastrowid
    conn.commit()
    conn.close()
    return nid


def get_notifications(user_id: int, path: str, unread_only: bool = False) -> list[dict]:
    conn = _connect(path)
    query = "SELECT * FROM notifications WHERE user_id = ?"
    if unread_only:
        query += " AND is_read = 0"
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        if d.get("data") and isinstance(d["data"], str):
            try:
                d["data"] = json.loads(d["data"])
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(d)
    return results


def mark_notification_read(notification_id: int, user_id: int, path: str) -> bool:
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
        (notification_id, user_id),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def mark_all_notifications_read(user_id: int, path: str) -> int:
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
        (user_id,),
    )
    count = cur.rowcount
    conn.commit()
    conn.close()
    return count
