"""Reepo growth database — repo events and changelog storage."""
from __future__ import annotations

from src.db import _connect, DEFAULT_DB_PATH

GROWTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS repo_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    data TEXT,
    occurred_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);

CREATE INDEX IF NOT EXISTS idx_repo_events_repo ON repo_events(repo_id);
CREATE INDEX IF NOT EXISTS idx_repo_events_type ON repo_events(event_type);
CREATE INDEX IF NOT EXISTS idx_repo_events_occurred ON repo_events(occurred_at DESC);
"""


def init_growth_db(path: str = DEFAULT_DB_PATH) -> None:
    """Initialize growth tables."""
    conn = _connect(path)
    conn.executescript(GROWTH_SCHEMA)
    conn.commit()
    conn.close()
