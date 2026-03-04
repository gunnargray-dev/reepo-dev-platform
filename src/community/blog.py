"""Reepo blog — create, publish, and serve blog posts with RSS feed."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from src.db import _connect, DEFAULT_DB_PATH


def create_post(
    slug: str,
    title: str,
    body: str,
    author: str,
    tags: list[str] | None = None,
    path: str = DEFAULT_DB_PATH,
) -> int:
    """Create a new blog post. Returns the post id."""
    conn = _connect(path)
    tags_json = json.dumps(tags or [])
    cur = conn.execute(
        "INSERT INTO blog_posts (slug, title, body, author, tags) VALUES (?, ?, ?, ?, ?)",
        (slug, title, body, author, tags_json),
    )
    post_id = cur.lastrowid
    conn.commit()
    conn.close()
    return post_id


def get_post(slug: str, path: str = DEFAULT_DB_PATH) -> dict | None:
    """Get a single blog post by slug."""
    conn = _connect(path)
    row = conn.execute(
        "SELECT * FROM blog_posts WHERE slug = ?", (slug,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    post = dict(row)
    if isinstance(post.get("tags"), str):
        try:
            post["tags"] = json.loads(post["tags"])
        except (json.JSONDecodeError, TypeError):
            post["tags"] = []
    return post


def list_posts(
    limit: int = 20,
    offset: int = 0,
    tag: str | None = None,
    published_only: bool = True,
    path: str = DEFAULT_DB_PATH,
) -> list[dict]:
    """List blog posts, optionally filtered by tag and publish status."""
    conn = _connect(path)
    clauses = []
    params: list = []
    if published_only:
        clauses.append("published_at IS NOT NULL")
    if tag:
        clauses.append("tags LIKE ?")
        params.append(f"%{tag}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM blog_posts {where} "
        "ORDER BY published_at DESC, created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        post = dict(row)
        if isinstance(post.get("tags"), str):
            try:
                post["tags"] = json.loads(post["tags"])
            except (json.JSONDecodeError, TypeError):
                post["tags"] = []
        results.append(post)
    return results


def update_post(
    slug: str,
    title: str | None = None,
    body: str | None = None,
    tags: list[str] | None = None,
    path: str = DEFAULT_DB_PATH,
) -> bool:
    """Update a blog post. Only provided fields are changed. Returns True if updated."""
    conn = _connect(path)
    updates = []
    params: list = []
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if body is not None:
        updates.append("body = ?")
        params.append(body)
    if tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(tags))
    if not updates:
        conn.close()
        return False
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(slug)
    cur = conn.execute(
        f"UPDATE blog_posts SET {', '.join(updates)} WHERE slug = ?",
        params,
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def publish_post(slug: str, path: str = DEFAULT_DB_PATH) -> bool:
    """Publish a post by setting published_at. Returns True if published."""
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE blog_posts SET published_at = CURRENT_TIMESTAMP, "
        "updated_at = CURRENT_TIMESTAMP WHERE slug = ? AND published_at IS NULL",
        (slug,),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def generate_rss_feed(posts: list[dict], site_url: str = "https://reepo.dev") -> str:
    """Generate an RSS 2.0 XML feed from a list of published posts."""
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for post in posts:
        pub_date = post.get("published_at", "")
        items.append(
            f"    <item>\n"
            f"      <title>{escape(post.get('title', ''))}</title>\n"
            f"      <link>{site_url}/blog/{escape(post.get('slug', ''))}</link>\n"
            f"      <description>{escape(post.get('body', '')[:200])}</description>\n"
            f"      <author>{escape(post.get('author', ''))}</author>\n"
            f"      <pubDate>{escape(pub_date)}</pubDate>\n"
            f"    </item>"
        )
    items_xml = "\n".join(items)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        "    <title>Reepo.dev Blog</title>\n"
        f"    <link>{site_url}/blog</link>\n"
        "    <description>Open source discovery engine for AI repos</description>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        f"{items_xml}\n"
        "  </channel>\n"
        "</rss>"
    )
