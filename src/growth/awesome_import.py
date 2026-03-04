"""Reepo awesome import — parse awesome lists and bulk import repos."""
from __future__ import annotations

import re

from src.db import _connect, DEFAULT_DB_PATH

_GITHUB_REPO_RE = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)"
)


def parse_awesome_list(markdown_content: str) -> list[dict]:
    """Parse an awesome list markdown and extract GitHub repo URLs."""
    results = []
    seen = set()
    for match in _GITHUB_REPO_RE.finditer(markdown_content):
        owner, name = match.group(1), match.group(2)
        name = name.rstrip("/")
        key = f"{owner}/{name}".lower()
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "owner": owner,
            "name": name,
            "full_name": f"{owner}/{name}",
            "url": f"https://github.com/{owner}/{name}",
        })
    return results


def import_from_url(raw_url: str) -> dict:
    """Import repos from an awesome list URL. Returns parsed repos."""
    # In production this would fetch the URL; here we validate format
    if not raw_url.startswith("http"):
        return {"ok": False, "error": "Invalid URL format"}
    return {"ok": True, "url": raw_url, "repos": []}


def bulk_import(github_urls: list[str], db_path: str = DEFAULT_DB_PATH) -> dict:
    """Bulk import GitHub repo URLs. Returns counts of imported/already_indexed/invalid."""
    conn = _connect(db_path)
    imported = 0
    already_indexed = 0
    invalid = 0

    for url in github_urls:
        match = _GITHUB_REPO_RE.match(url)
        if not match:
            invalid += 1
            continue

        owner, name = match.group(1), match.group(2)
        name = name.rstrip("/")

        existing = conn.execute(
            "SELECT id FROM repos WHERE owner = ? AND name = ?",
            (owner, name),
        ).fetchone()
        if existing:
            already_indexed += 1
            continue

        conn.execute(
            "INSERT INTO repos (github_id, owner, name, full_name, stars, language, category_primary) "
            "VALUES (NULL, ?, ?, ?, 0, NULL, NULL)",
            (owner, name, f"{owner}/{name}"),
        )
        imported += 1

    conn.commit()
    conn.close()
    return {"imported": imported, "already_indexed": already_indexed, "invalid": invalid}
