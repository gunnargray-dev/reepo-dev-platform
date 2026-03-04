"""Reepo community database — tables for Built With, comments, submissions, blog, digest."""
from __future__ import annotations

from src.db import _connect, DEFAULT_DB_PATH

COMMUNITY_SCHEMA = """
CREATE TABLE IF NOT EXISTS built_with (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    repo_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT,
    screenshot_url TEXT,
    status TEXT DEFAULT 'pending',
    upvote_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS built_with_repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    built_with_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    FOREIGN KEY (built_with_id) REFERENCES built_with(id),
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS upvotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    built_with_id INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, built_with_id),
    FOREIGN KEY (built_with_id) REFERENCES built_with(id)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    parent_id INTEGER,
    body TEXT NOT NULL,
    is_flagged INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS repo_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    github_url TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    reviewed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blog_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    author TEXT NOT NULL,
    tags TEXT DEFAULT '[]',
    published_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS digest_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_number INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    sent_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_built_with_status ON built_with(status);
CREATE INDEX IF NOT EXISTS idx_built_with_user ON built_with(user_id);
CREATE INDEX IF NOT EXISTS idx_built_with_repos_bw ON built_with_repos(built_with_id);
CREATE INDEX IF NOT EXISTS idx_built_with_repos_repo ON built_with_repos(repo_id);
CREATE INDEX IF NOT EXISTS idx_upvotes_bw ON upvotes(built_with_id);
CREATE INDEX IF NOT EXISTS idx_upvotes_user ON upvotes(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_repo ON comments(repo_id);
CREATE INDEX IF NOT EXISTS idx_comments_flagged ON comments(is_flagged);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON repo_submissions(status);
CREATE INDEX IF NOT EXISTS idx_blog_slug ON blog_posts(slug);
CREATE INDEX IF NOT EXISTS idx_blog_published ON blog_posts(published_at);
CREATE INDEX IF NOT EXISTS idx_digest_number ON digest_issues(issue_number);
"""


def init_community_db(path: str = DEFAULT_DB_PATH) -> None:
    """Create all community tables."""
    conn = _connect(path)
    conn.executescript(COMMUNITY_SCHEMA)
    conn.commit()
    conn.close()
