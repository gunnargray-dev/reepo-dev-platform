"""Reepo API — search routes.

Supports transparent NL routing via the optional `mode` parameter:
  - keyword (default): existing FTS5 keyword search.
  - ai: always route through the AI build pipeline.
  - auto: classify the query; NL queries route through AI, keywords stay FTS.
"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.middleware import search_cache
from src.search import search
from src.api.search_classifier import is_natural_language
from src.api.build import run_build_pipeline_sync
from src.db import _connect

router = APIRouter()

_VALID_MODES = {"keyword", "ai", "auto"}

# Repo card fields surfaced for AI-mode picks.
_PICK_REPO_COLS = (
    "id, full_name, description, stars, reepo_score, language, "
    "topics, category_primary, license, updated_at"
)


def _enrich_picks(picks: list[dict], db_path: str) -> list[dict]:
    """Augment AI picks with repo metadata for frontend rendering."""
    if not picks:
        return []
    ids = [p["repo_id"] for p in picks if isinstance(p.get("repo_id"), int)]
    if not ids:
        return picks
    conn = _connect(db_path)
    try:
        placeholders = ",".join("?" * len(ids))
        rows = conn.execute(
            f"SELECT {_PICK_REPO_COLS} FROM repos WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
    finally:
        conn.close()
    by_id = {r["id"]: dict(r) for r in rows}
    enriched: list[dict] = []
    for p in picks:
        rid = p.get("repo_id")
        repo_meta = by_id.get(rid, {})
        # owner/name split for frontend convenience
        full_name = repo_meta.get("full_name") or p.get("repo") or ""
        owner, _, name = full_name.partition("/")
        enriched.append({
            **p,
            "id": rid,
            "owner": owner,
            "name": name,
            "full_name": full_name,
            "description": repo_meta.get("description"),
            "stars": repo_meta.get("stars"),
            "reepo_score": repo_meta.get("reepo_score"),
            "language": repo_meta.get("language"),
            "topics": repo_meta.get("topics"),
            "category_primary": repo_meta.get("category_primary"),
            "license": repo_meta.get("license"),
            "updated_at": repo_meta.get("updated_at"),
        })
    return enriched


@router.get("/api/search")
def api_search(
    q: str = Query("", description="Search query"),
    category: str | None = Query(None, description="Filter by category"),
    language: str | None = Query(None, description="Filter by language"),
    min_score: int = Query(0, ge=0, le=100, description="Minimum Reepo Score"),
    sort: str = Query("relevance", description="Sort by: relevance, stars, score, newest"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    mode: str = Query("keyword", description="Routing mode: keyword | ai | auto"),
):
    from src.server import get_db_path

    db_path = get_db_path()

    if mode not in _VALID_MODES:
        return JSONResponse(
            status_code=400,
            content={"error": f"invalid mode '{mode}', must be one of {sorted(_VALID_MODES)}"},
        )

    # Decide effective mode.
    if mode == "auto":
        effective = "ai" if is_natural_language(q) else "keyword"
    else:
        effective = mode

    if effective == "ai":
        if not q or not q.strip():
            return JSONResponse(status_code=400, content={"error": "query is required"})

        cache_key = search_cache.make_key("search:ai", q=q.strip())
        cached = search_cache.get(cache_key)
        if cached is not None:
            return cached

        result = run_build_pipeline_sync(q, path=db_path)
        if result.get("error") and not result.get("picks"):
            return JSONResponse(
                status_code=503,
                content={
                    "mode": "ai",
                    "query": result.get("query", q),
                    "error": result["error"],
                    "picks": [],
                    "degraded": True,
                },
            )

        picks = _enrich_picks(result.get("picks", []), db_path)
        response = {
            "mode": "ai",
            "query": result.get("query", q),
            "intent": result.get("intent", {}),
            "picks": picks,
            "notes": result.get("notes", ""),
            "degraded": bool(result.get("degraded")),
        }
        # Short in-memory cache layer on top of ai_query_cache (which already
        # dedupes Anthropic calls). 5min keeps response identical for a burst.
        search_cache.set(cache_key, response, ttl=300)
        return response

    # ----- keyword mode -----
    cache_key = search_cache.make_key(
        "search", q=q, category=category, language=language,
        min_score=min_score, sort=sort, page=page, per_page=per_page,
    )
    cached = search_cache.get(cache_key)
    if cached is not None:
        # Ensure mode field present even on cached payloads.
        if isinstance(cached, dict) and cached.get("mode") != "keyword":
            cached = {**cached, "mode": "keyword"}
        return cached

    result = search(
        path=db_path,
        query=q,
        category=category,
        language=language,
        min_score=min_score,
        sort=sort,
        page=page,
        per_page=per_page,
    )
    result["mode"] = "keyword"

    search_cache.set(cache_key, result, ttl=300)
    return result
