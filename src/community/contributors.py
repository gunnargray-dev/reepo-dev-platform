"""Reepo contributor program — roles, badges, and permissions."""
from __future__ import annotations

from src.db import _connect, DEFAULT_DB_PATH


CONTRIBUTOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS contributor_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER
);

CREATE INDEX IF NOT EXISTS idx_contributor_user ON contributor_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_contributor_role ON contributor_roles(role);
"""

VALID_ROLES = {"moderator", "contributor", "verified_author"}

ROLE_PERMISSIONS = {
    "moderator": ["approve_repos", "moderate_comments", "view_reports"],
    "contributor": ["pro_access", "badge_display"],
    "verified_author": ["badge_display", "author_highlight"],
}


def init_contributor_db(path: str = DEFAULT_DB_PATH) -> None:
    """Create contributor tables."""
    conn = _connect(path)
    conn.executescript(CONTRIBUTOR_SCHEMA)
    conn.commit()
    conn.close()


def grant_role(
    user_id: int, role: str, granted_by: int | None = None, path: str = DEFAULT_DB_PATH
) -> bool:
    """Grant a role to a user. Returns True if newly granted."""
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}. Must be one of {VALID_ROLES}")
    conn = _connect(path)
    existing = conn.execute(
        "SELECT id FROM contributor_roles WHERE user_id = ? AND role = ?",
        (user_id, role),
    ).fetchone()
    if existing:
        conn.close()
        return False
    conn.execute(
        "INSERT INTO contributor_roles (user_id, role, granted_by) VALUES (?, ?, ?)",
        (user_id, role, granted_by),
    )
    conn.commit()
    conn.close()
    return True


def revoke_role(user_id: int, role: str, path: str = DEFAULT_DB_PATH) -> bool:
    """Revoke a role from a user. Returns True if was granted."""
    conn = _connect(path)
    cur = conn.execute(
        "DELETE FROM contributor_roles WHERE user_id = ? AND role = ?",
        (user_id, role),
    )
    removed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def get_user_roles(user_id: int, path: str = DEFAULT_DB_PATH) -> list[str]:
    """Get all roles for a user."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT role FROM contributor_roles WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return [r["role"] for r in rows]


def get_user_badges(user_id: int, path: str = DEFAULT_DB_PATH) -> list[dict]:
    """Get badge display info for a user."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT role, granted_at FROM contributor_roles WHERE user_id = ? ORDER BY granted_at",
        (user_id,),
    ).fetchall()
    conn.close()

    badges = []
    badge_config = {
        "moderator": {"label": "Moderator", "color": "blue", "icon": "shield"},
        "contributor": {"label": "Contributor", "color": "green", "icon": "heart"},
        "verified_author": {"label": "Verified Author", "color": "purple", "icon": "check"},
    }
    for row in rows:
        config = badge_config.get(row["role"], {"label": row["role"], "color": "gray", "icon": "star"})
        badges.append({
            "role": row["role"],
            "label": config["label"],
            "color": config["color"],
            "icon": config["icon"],
            "granted_at": row["granted_at"],
        })
    return badges


def has_permission(user_id: int, permission: str, path: str = DEFAULT_DB_PATH) -> bool:
    """Check if a user has a specific permission via any of their roles."""
    roles = get_user_roles(user_id, path)
    for role in roles:
        if permission in ROLE_PERMISSIONS.get(role, []):
            return True
    return False


def is_moderator(user_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Check if a user is a moderator."""
    return "moderator" in get_user_roles(user_id, path)


def get_contributors_by_role(role: str, path: str = DEFAULT_DB_PATH) -> list[dict]:
    """Get all users with a specific role."""
    if role not in VALID_ROLES:
        return []
    conn = _connect(path)
    rows = conn.execute(
        "SELECT user_id, role, granted_at, granted_by FROM contributor_roles WHERE role = ?",
        (role,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
