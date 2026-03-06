"""Reepo API — category routes."""
import json
from collections import Counter

from fastapi import APIRouter, Query

from src.db import get_categories, get_repos_by_category, list_repos, _connect

router = APIRouter()


@router.get("/api/categories")
def api_categories():
    from src.server import get_db_path

    db_path = get_db_path()
    categories = get_categories(db_path)
    counts = get_repos_by_category(db_path)

    for cat in categories:
        cat["repo_count"] = counts.get(cat["slug"], 0)

    return {"categories": categories}


@router.get("/api/categories/{slug}/tags")
def api_category_tags(
    slug: str,
    limit: int = Query(20, ge=1, le=50),
):
    """Return the most common topic tags for repos in a category."""
    from src.server import get_db_path

    db_path = get_db_path()
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT topics FROM repos WHERE category_primary = ? AND topics IS NOT NULL AND topics != ''",
        (slug,),
    ).fetchall()
    conn.close()

    counter: Counter[str] = Counter()
    # Generic tags to exclude (too broad to be useful as filters)
    exclude = {
        "ai", "machine-learning", "deep-learning", "python", "ml",
        "artificial-intelligence", "open-source", "hacktoberfest",
        "awesome", "awesome-list", "python3", "data-science",
        "typescript", "javascript", "golang", "rust", "java", "cpp",
        "python-library", "python-3", "c-plus-plus",
    }
    for row in rows:
        raw = row["topics"] if isinstance(row, dict) else row[0]
        if not raw:
            continue
        try:
            parsed = json.loads(raw) if raw.startswith("[") else [t.strip() for t in raw.split(",")]
        except (json.JSONDecodeError, TypeError):
            continue
        for tag in parsed:
            tag = tag.lower().strip()
            if tag and tag not in exclude:
                counter[tag] += 1

    # Deduplicate near-identical tags (plural/singular, hyphenated variants)
    seen_stems: dict[str, str] = {}
    merged: Counter[str] = Counter()
    for tag, count in counter.most_common():
        stem = tag.rstrip("s").replace("-", "")
        if stem in seen_stems:
            merged[seen_stems[stem]] += count
        else:
            seen_stems[stem] = tag
            merged[tag] = count

    # Only return tags that appear in at least 3 repos
    results = [
        {"tag": tag, "count": count}
        for tag, count in merged.most_common(limit)
        if count >= 3
    ]
    return {"tags": results, "category": slug}


@router.get("/api/categories/{slug}/repos")
def api_category_repos(
    slug: str,
    sort_by: str = Query("stars"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    from src.server import get_db_path

    db_path = get_db_path()
    repos = list_repos(path=db_path, category=slug, sort_by=sort_by, limit=limit, offset=offset)
    return {"repos": repos, "category": slug, "count": len(repos)}
