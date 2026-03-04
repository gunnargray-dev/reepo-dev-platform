"""Reepo weekly digest — compile trending repos, new additions, and top projects."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from src.db import _connect, _row_to_dict, DEFAULT_DB_PATH


def generate_digest(path: str = DEFAULT_DB_PATH) -> dict:
    """Auto-compile weekly digest: top trending, new additions, top Built With."""
    conn = _connect(path)

    # Top 10 trending repos by stars
    trending = conn.execute(
        "SELECT * FROM repos ORDER BY stars DESC LIMIT 10"
    ).fetchall()

    # Top 5 new additions by indexed_at
    new_additions = conn.execute(
        "SELECT * FROM repos ORDER BY indexed_at DESC LIMIT 5"
    ).fetchall()

    # Top Built With submissions
    top_projects = conn.execute(
        "SELECT * FROM built_with WHERE status = 'approved' "
        "ORDER BY upvote_count DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trending_repos": [_row_to_dict(r) for r in trending],
        "new_additions": [_row_to_dict(r) for r in new_additions],
        "top_projects": [dict(r) for r in top_projects],
    }


def render_digest_html(digest_data: dict) -> str:
    """Render digest data as HTML for email or web display."""
    html_parts = [
        "<html><body>",
        "<h1>Reepo Weekly Digest</h1>",
        f"<p>Generated: {digest_data['generated_at']}</p>",
        "<h2>Trending Repos</h2><ol>",
    ]
    for repo in digest_data.get("trending_repos", []):
        html_parts.append(
            f"<li><strong>{repo.get('full_name', 'unknown')}</strong> "
            f"— {repo.get('description', '')} "
            f"({repo.get('stars', 0):,} stars)</li>"
        )
    html_parts.append("</ol>")

    html_parts.append("<h2>New Additions</h2><ol>")
    for repo in digest_data.get("new_additions", []):
        html_parts.append(
            f"<li><strong>{repo.get('full_name', 'unknown')}</strong> "
            f"— {repo.get('description', '')}</li>"
        )
    html_parts.append("</ol>")

    html_parts.append("<h2>Top Built With Projects</h2><ol>")
    for project in digest_data.get("top_projects", []):
        html_parts.append(
            f"<li><strong>{project.get('title', 'Untitled')}</strong> "
            f"— {project.get('description', '')} "
            f"({project.get('upvote_count', 0)} upvotes)</li>"
        )
    html_parts.append("</ol></body></html>")

    return "\n".join(html_parts)


def render_digest_markdown(digest_data: dict) -> str:
    """Render digest data as Markdown for blog publishing."""
    lines = [
        "# Reepo Weekly Digest",
        "",
        f"*Generated: {digest_data['generated_at']}*",
        "",
        "## Trending Repos",
        "",
    ]
    for i, repo in enumerate(digest_data.get("trending_repos", []), 1):
        lines.append(
            f"{i}. **{repo.get('full_name', 'unknown')}** "
            f"— {repo.get('description', '')} "
            f"({repo.get('stars', 0):,} stars)"
        )

    lines.extend(["", "## New Additions", ""])
    for i, repo in enumerate(digest_data.get("new_additions", []), 1):
        lines.append(
            f"{i}. **{repo.get('full_name', 'unknown')}** "
            f"— {repo.get('description', '')}"
        )

    lines.extend(["", "## Top Built With Projects", ""])
    for i, project in enumerate(digest_data.get("top_projects", []), 1):
        lines.append(
            f"{i}. **{project.get('title', 'Untitled')}** "
            f"— {project.get('description', '')} "
            f"({project.get('upvote_count', 0)} upvotes)"
        )

    return "\n".join(lines)


def save_digest(digest_data: dict, path: str = DEFAULT_DB_PATH) -> int:
    """Save a digest issue to the database. Returns the digest id."""
    conn = _connect(path)

    # Get next issue number
    row = conn.execute(
        "SELECT MAX(issue_number) as max_num FROM digest_issues"
    ).fetchone()
    next_number = (row["max_num"] or 0) + 1

    content = json.dumps(digest_data)
    cur = conn.execute(
        "INSERT INTO digest_issues (issue_number, title, content, sent_at) "
        "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        (next_number, f"Reepo Weekly Digest #{next_number}", content),
    )
    digest_id = cur.lastrowid
    conn.commit()
    conn.close()
    return digest_id


def get_latest_digest(path: str = DEFAULT_DB_PATH) -> dict | None:
    """Get the most recent digest issue."""
    conn = _connect(path)
    row = conn.execute(
        "SELECT * FROM digest_issues ORDER BY issue_number DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    try:
        result["content"] = json.loads(result["content"])
    except (json.JSONDecodeError, TypeError):
        pass
    return result
