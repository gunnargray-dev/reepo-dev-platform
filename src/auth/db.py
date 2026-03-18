"""Reepo auth database — users, sessions, and API keys."""
import secrets
import sqlite3
from pathlib import Path

AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    github_id INTEGER UNIQUE,
    email TEXT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    is_pro BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    refresh_token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    daily_limit INTEGER DEFAULT 100,
    requests_today INTEGER DEFAULT 0,
    last_reset_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
"""


def _connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_auth_db(path: str) -> None:
    conn = _connect(path)
    conn.executescript(AUTH_SCHEMA)
    # Migration: add supabase_id column if it doesn't exist yet
    try:
        conn.execute("ALTER TABLE users ADD COLUMN supabase_id TEXT UNIQUE")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.close()


# --- Users ---

def create_user(
    username: str,
    path: str,
    github_id: int | None = None,
    email: str | None = None,
    display_name: str | None = None,
    avatar_url: str | None = None,
    bio: str | None = None,
) -> int:
    conn = _connect(path)
    cur = conn.execute(
        "INSERT INTO users (github_id, email, username, display_name, avatar_url, bio) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (github_id, email, username, display_name, avatar_url, bio),
    )
    uid = cur.lastrowid
    conn.commit()
    conn.close()
    return uid


def get_user_by_id(user_id: int, path: str) -> dict | None:
    conn = _connect(path)
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username: str, path: str) -> dict | None:
    conn = _connect(path)
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_github_id(github_id: int, path: str) -> dict | None:
    conn = _connect(path)
    row = conn.execute("SELECT * FROM users WHERE github_id = ?", (github_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user(user_id: int, path: str, **kwargs) -> bool:
    if not kwargs:
        return False
    allowed = {"email", "username", "display_name", "avatar_url", "bio", "is_pro"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return False
    sets = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [user_id]
    conn = _connect(path)
    cur = conn.execute(
        f"UPDATE users SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        vals,
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def get_or_create_user(
    supabase_id: str,
    email: str | None,
    username: str | None,
    avatar_url: str | None,
    path: str,
) -> dict:
    """Find user by supabase_id, updating fields if changed. Create if not found."""
    conn = _connect(path)
    row = conn.execute(
        "SELECT * FROM users WHERE supabase_id = ?", (supabase_id,)
    ).fetchone()

    if row:
        user = dict(row)
        updates = {}
        if email is not None and email != user.get("email"):
            updates["email"] = email
        if username is not None and username != user.get("username"):
            updates["username"] = username
        if avatar_url is not None and avatar_url != user.get("avatar_url"):
            updates["avatar_url"] = avatar_url
        if updates:
            sets = ", ".join(f"{k} = ?" for k in updates)
            vals = list(updates.values()) + [user["id"]]
            conn.execute(
                f"UPDATE users SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                vals,
            )
            conn.commit()
            # Re-fetch after update
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user["id"],)
            ).fetchone()
            user = dict(row)
        conn.close()
        return user

    # Create new user
    cur = conn.execute(
        "INSERT INTO users (supabase_id, email, username, avatar_url) VALUES (?, ?, ?, ?)",
        (supabase_id, email, username or supabase_id[:8], avatar_url),
    )
    new_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return dict(row)


def delete_user(user_id: int, path: str) -> bool:
    conn = _connect(path)
    cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


# --- Sessions ---

def create_session(user_id: int, token: str, refresh_token: str, expires_at: str, path: str) -> int:
    conn = _connect(path)
    cur = conn.execute(
        "INSERT INTO sessions (user_id, token, refresh_token, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, token, refresh_token, expires_at),
    )
    sid = cur.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_session_by_token(token: str, path: str) -> dict | None:
    conn = _connect(path)
    row = conn.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_session_by_refresh(refresh_token: str, path: str) -> dict | None:
    conn = _connect(path)
    row = conn.execute(
        "SELECT * FROM sessions WHERE refresh_token = ?", (refresh_token,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(token: str, path: str) -> bool:
    conn = _connect(path)
    cur = conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def delete_user_sessions(user_id: int, path: str) -> int:
    conn = _connect(path)
    cur = conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    count = cur.rowcount
    conn.commit()
    conn.close()
    return count


# --- API Keys ---

def create_api_key(user_id: int, name: str, path: str, daily_limit: int = 100) -> dict:
    key = f"rp_{secrets.token_hex(24)}"
    conn = _connect(path)
    cur = conn.execute(
        "INSERT INTO api_keys (user_id, key, name, daily_limit) VALUES (?, ?, ?, ?)",
        (user_id, key, name, daily_limit),
    )
    key_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": key_id, "key": key, "name": name, "daily_limit": daily_limit}


def get_api_keys_for_user(user_id: int, path: str) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_api_key(key: str, path: str) -> dict | None:
    conn = _connect(path)
    row = conn.execute("SELECT * FROM api_keys WHERE key = ?", (key,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_api_key(key_id: int, user_id: int, path: str) -> bool:
    conn = _connect(path)
    cur = conn.execute(
        "DELETE FROM api_keys WHERE id = ? AND user_id = ?", (key_id, user_id)
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def increment_api_key_usage(key: str, path: str) -> bool:
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE api_keys SET requests_today = requests_today + 1 WHERE key = ? AND is_active = 1",
        (key,),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def reset_api_key_usage(key: str, path: str) -> bool:
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE api_keys SET requests_today = 0, last_reset_at = CURRENT_TIMESTAMP WHERE key = ?",
        (key,),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed
