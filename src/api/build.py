"""POST /api/build — AI-native build recommender (SSE stream).

Pipeline:
  1. Cache check (ai_query_cache, 24h TTL)
  2. Intent extraction (Claude Haiku) -> capabilities/constraints/language/scale
  3. Hybrid retrieval: vector (Voyage + sqlite-vec) + FTS5, merged via RRF
  4. Structural rerank: reepo_score, language match, freshness
  5. Stack composition (Claude Sonnet, streaming, prompt caching)
  6. Cache write
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import struct
from datetime import datetime, timezone, timedelta
from typing import Any, Iterable

import anthropic
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from src.db import _connect
from src import embeddings as emb_mod
from src.search import search as fts_search

logger = logging.getLogger(__name__)

router = APIRouter()

HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-6"
CACHE_TTL = timedelta(hours=24)
RRF_K = 60
CANDIDATE_LIMIT = 50
RERANK_LIMIT = 20


class BuildRequest(BaseModel):
    query: str


def _db_path() -> str:
    from src.server import get_db_path
    return get_db_path()


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _hash_query(q: str) -> str:
    return hashlib.sha256(q.strip().lower().encode("utf-8")).hexdigest()


# ---------- cache ----------

def _cache_get(query_hash: str, path: str) -> list[tuple[str, dict]] | None:
    conn = _connect(path)
    try:
        row = conn.execute(
            "SELECT response_json, created_at FROM ai_query_cache WHERE query_hash = ?",
            (query_hash,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    try:
        created = datetime.fromisoformat(row["created_at"])
    except ValueError:
        return None
    if datetime.now(timezone.utc) - created > CACHE_TTL:
        return None
    try:
        events = json.loads(row["response_json"])
    except json.JSONDecodeError:
        return None
    return [(e["event"], e["data"]) for e in events]


def _cache_set(query_hash: str, query: str, events: list[tuple[str, dict]], path: str) -> None:
    conn = _connect(path)
    try:
        payload = json.dumps([{"event": e, "data": d} for e, d in events])
        conn.execute(
            "INSERT OR REPLACE INTO ai_query_cache (query_hash, query, response_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (query_hash, query, payload, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


# ---------- intent ----------

_INTENT_PROMPT = """Extract a structured intent from the user's build request.

Query: {query}

Return ONLY a JSON object with these keys:
- capabilities: array of short strings describing desired capabilities
- constraints: array of short strings describing constraints (e.g. "local-only", "open-source")
- language: preferred programming language or null
- scale: "small" | "medium" | "large" | null

Return ONLY the JSON object, nothing else."""


def _extract_intent(query: str, client: anthropic.Anthropic) -> dict:
    default = {"capabilities": [], "constraints": [], "language": None, "scale": None}
    try:
        resp = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": _INTENT_PROMPT.format(query=query)}],
        )
        text = resp.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            text = text.rsplit("```", 1)[0]
        data = json.loads(text)
        return {
            "capabilities": [str(c) for c in data.get("capabilities", []) if c][:10],
            "constraints": [str(c) for c in data.get("constraints", []) if c][:10],
            "language": data.get("language"),
            "scale": data.get("scale"),
        }
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.debug("intent parse failure: %s", e)
    except anthropic.APIError as e:
        logger.warning("Anthropic intent error: %s", e)
    return default


# ---------- retrieval ----------

def _vec_search(query_text: str, path: str) -> list[tuple[int, float]]:
    """Return [(repo_id, distance)] from vector search, or [] on any failure."""
    if not os.environ.get("VOYAGE_API_KEY"):
        return []
    conn = _connect(path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM repo_embeddings"
        ).fetchone()
        if not row or row["n"] == 0:
            return []
        try:
            vec = emb_mod.embed_query(query_text)
        except Exception as e:  # noqa: BLE001
            logger.warning("embed_query failed: %s", e)
            return []
        blob = struct.pack(f"{len(vec)}f", *vec)
        rows = conn.execute(
            "SELECT repo_id, distance FROM repo_embeddings "
            "WHERE embedding MATCH ? AND k = ? ORDER BY distance",
            (blob, CANDIDATE_LIMIT),
        ).fetchall()
        return [(r["repo_id"], r["distance"]) for r in rows]
    except Exception as e:  # noqa: BLE001
        logger.warning("vec search failed: %s", e)
        return []
    finally:
        conn.close()


def _fts_candidates(query: str, path: str) -> list[int]:
    if not query.strip():
        return []
    # Limit FTS search to top CANDIDATE_LIMIT.
    try:
        result = fts_search(
            path=path, query=query, sort="relevance", page=1, per_page=CANDIDATE_LIMIT
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("fts search failed: %s", e)
        return []
    return [r["id"] for r in result.get("results", [])]


def _rrf_merge(vec_ids: list[int], fts_ids: list[int]) -> list[int]:
    scores: dict[int, float] = {}
    for rank, rid in enumerate(vec_ids):
        scores[rid] = scores.get(rid, 0.0) + 1.0 / (RRF_K + rank + 1)
    for rank, rid in enumerate(fts_ids):
        scores[rid] = scores.get(rid, 0.0) + 1.0 / (RRF_K + rank + 1)
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [rid for rid, _ in ordered[:CANDIDATE_LIMIT]]


# ---------- rerank ----------

def _load_repos(repo_ids: list[int], path: str) -> list[dict]:
    if not repo_ids:
        return []
    conn = _connect(path)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(repos)").fetchall()}
        has_use_cases = "use_cases" in cols
        select_cols = (
            "id, owner, name, full_name, description, topics, stars, reepo_score, "
            "language, license, updated_at, category_primary"
            + (", use_cases" if has_use_cases else "")
        )
        placeholders = ",".join("?" * len(repo_ids))
        rows = conn.execute(
            f"SELECT {select_cols} FROM repos WHERE id IN ({placeholders})",
            repo_ids,
        ).fetchall()
    finally:
        conn.close()
    order = {rid: i for i, rid in enumerate(repo_ids)}
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["topics"] = json.loads(d.get("topics") or "[]")
        except (json.JSONDecodeError, TypeError):
            d["topics"] = []
        if "use_cases" in d:
            try:
                d["use_cases"] = json.loads(d["use_cases"] or "[]")
            except (json.JSONDecodeError, TypeError):
                d["use_cases"] = []
        out.append(d)
    out.sort(key=lambda x: order.get(x["id"], 10**9))
    return out


def _structural_rerank(repos: list[dict], intent: dict) -> list[dict]:
    now = datetime.now(timezone.utc)
    lang_pref = (intent.get("language") or "").lower() or None

    def freshness(updated: str | None) -> float:
        if not updated:
            return 0.0
        try:
            dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            days = max(0.0, (now - dt).days)
            return max(0.0, 1.0 - days / 730.0)  # 2-year half-scale
        except ValueError:
            return 0.0

    def score(r: dict) -> float:
        base = (r.get("reepo_score") or 0) / 100.0
        lang_match = 0.25 if lang_pref and (r.get("language") or "").lower() == lang_pref else 0.0
        return base + lang_match + 0.15 * freshness(r.get("updated_at"))

    repos_sorted = sorted(repos, key=score, reverse=True)
    return repos_sorted[:RERANK_LIMIT]


# ---------- stack composition ----------

_SYSTEM_PROMPT = """You are reepo's stack composer. Given the user's intent and a list of candidate GitHub repositories, select 3-6 repos that together form a cohesive stack for what the user wants to build.

Output rules:
- Output ONE pick per line as a single-line JSON object: {"repo_id": <int>, "role": "<short label>", "why": "<1-2 sentences>"}
- `role` is a short label like "LLM runtime", "vector store", "agent framework", "UI framework".
- `why` cites concrete features from the candidate description/topics/use_cases.
- Only pick from the provided candidate list; repo_id MUST match a candidate's id.
- Do NOT include any prose, markdown, or wrapping array — just JSON objects, one per line.
- After the last pick, output a single JSON line: {"notes": "<optional 1-sentence overall note>"}"""


def _candidate_block(intent: dict, repos: list[dict]) -> str:
    lines = ["USER INTENT:", json.dumps(intent), "", "CANDIDATES:"]
    for r in repos:
        lines.append(
            json.dumps({
                "id": r["id"],
                "repo": r.get("full_name"),
                "description": (r.get("description") or "")[:280],
                "topics": (r.get("topics") or [])[:8],
                "language": r.get("language"),
                "reepo_score": r.get("reepo_score"),
                "use_cases": (r.get("use_cases") or [])[:4] if "use_cases" in r else [],
            })
        )
    return "\n".join(lines)


_JSON_LINE_RE = re.compile(r"\{[^\n]*\}")


def _enrich_pick(repo: dict, role: str, why: str) -> dict:
    """Build the canonical pick payload from a loaded repo row.

    Shared by the SSE stream and the sync pipeline so the two paths can't
    drift. Includes the enriched repo card fields the frontend needs.
    """
    return {
        "repo_id": repo["id"],
        "repo": repo.get("full_name"),
        "role": str(role or "")[:60],
        "why": str(why or "")[:500],
        "id": repo["id"],
        "owner": repo.get("owner"),
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "description": repo.get("description"),
        "stars": repo.get("stars"),
        "reepo_score": repo.get("reepo_score"),
        "language": repo.get("language"),
        "topics": repo.get("topics") or [],
        "category_primary": repo.get("category_primary"),
        "license": repo.get("license"),
        "updated_at": repo.get("updated_at"),
    }


def _parse_pick_lines(buf: str) -> tuple[list[dict], str]:
    """Return (complete_objects, remaining_buffer). Split on newlines."""
    picks: list[dict] = []
    if "\n" not in buf:
        return picks, buf
    *lines, tail = buf.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = _JSON_LINE_RE.search(line)
        if not m:
            continue
        try:
            picks.append(json.loads(m.group(0)))
        except json.JSONDecodeError:
            continue
    return picks, tail


def _compose_stack_stream(
    intent: dict,
    repos: list[dict],
    client: anthropic.Anthropic,
) -> Iterable[dict]:
    """Yield parsed JSON lines streamed from Claude. Final yield is sentinel with `__final` key."""
    valid_ids = {r["id"] for r in repos}
    repo_lookup = {r["id"]: r for r in repos}
    notes: str | None = None
    emitted = 0

    candidate_text = _candidate_block(intent, repos)
    try:
        with client.messages.stream(
            model=SONNET_MODEL,
            max_tokens=1500,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": candidate_text,
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            messages=[{"role": "user", "content": "Produce the stack now."}],
        ) as stream:
            buf = ""
            for chunk in stream.text_stream:
                buf += chunk
                parsed, buf = _parse_pick_lines(buf)
                for obj in parsed:
                    if "notes" in obj and "repo_id" not in obj:
                        notes = str(obj.get("notes") or "")
                        continue
                    rid = obj.get("repo_id")
                    if not isinstance(rid, int) or rid not in valid_ids:
                        continue
                    repo = repo_lookup[rid]
                    emitted += 1
                    yield _enrich_pick(repo, obj.get("role"), obj.get("why"))
            # flush trailing line
            if buf.strip():
                m = _JSON_LINE_RE.search(buf)
                if m:
                    try:
                        obj = json.loads(m.group(0))
                        if "notes" in obj and "repo_id" not in obj:
                            notes = str(obj.get("notes") or "")
                        else:
                            rid = obj.get("repo_id")
                            if isinstance(rid, int) and rid in valid_ids:
                                repo = repo_lookup[rid]
                                emitted += 1
                                yield _enrich_pick(repo, obj.get("role"), obj.get("why"))
                    except json.JSONDecodeError:
                        pass
    except anthropic.APIError as e:
        logger.warning("Anthropic compose error: %s", e)

    yield {"__final": True, "total_picks": emitted, "notes": notes or ""}


# ---------- sync pipeline (shared with /api/search ai-mode) ----------

def run_build_pipeline_sync(query: str, path: str | None = None) -> dict:
    """Run the full build pipeline synchronously and return a JSON-shaped dict.

    Used by GET /api/search when routing NL queries through AI. Honors the same
    ai_query_cache as the SSE endpoint so identical queries from either route
    share a 24h TTL cache entry.

    Returns:
      {
        "query": str,
        "intent": dict,
        "picks": [ {"repo_id": int, "repo": str, "role": str, "why": str}, ... ],
        "degraded": bool,
        "notes": str,
        "cached": bool,
        "error": Optional[str],
      }
    """
    query = (query or "").strip()
    if not query:
        return {
            "query": "",
            "intent": {},
            "picks": [],
            "degraded": False,
            "notes": "",
            "cached": False,
            "error": "query is required",
        }

    if path is None:
        path = _db_path()

    qhash = _hash_query(query)
    cached = _cache_get(qhash, path)
    if cached is not None:
        intent: dict = {}
        picks: list[dict] = []
        notes = ""
        degraded = False
        for event, data in cached:
            if event == "intent":
                intent = data or {}
            elif event == "candidates":
                if data.get("degraded"):
                    degraded = True
            elif event == "degraded":
                if data.get("degraded"):
                    degraded = True
            elif event == "pick":
                picks.append(data)
            elif event == "done":
                notes = data.get("notes", "") or ""
        return {
            "query": query,
            "intent": intent,
            "picks": picks,
            "degraded": degraded,
            "notes": notes,
            "cached": True,
            "error": None,
        }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "query": query,
            "intent": {},
            "picks": [],
            "degraded": True,
            "notes": "",
            "cached": False,
            "error": "ANTHROPIC_API_KEY not configured",
        }

    try:
        ai_client = anthropic.Anthropic(api_key=api_key)
    except Exception as e:  # noqa: BLE001
        return {
            "query": query,
            "intent": {},
            "picks": [],
            "degraded": True,
            "notes": "",
            "cached": False,
            "error": f"anthropic client init failed: {e}",
        }

    events: list[tuple[str, dict]] = []

    intent = _extract_intent(query, ai_client)
    events.append(("intent", intent))

    vec_query_text = query + " " + " ".join(intent.get("capabilities", []))
    vec_hits = _vec_search(vec_query_text, path)
    fts_ids = _fts_candidates(query, path)
    vec_available = bool(vec_hits)
    if not vec_available:
        events.append(("degraded", {"degraded": True, "reason": "vector_search_unavailable"}))

    merged = _rrf_merge([v[0] for v in vec_hits], fts_ids)
    if not merged and fts_ids:
        merged = fts_ids[:CANDIDATE_LIMIT]
    events.append(("candidates", {"repo_ids": merged, "degraded": not vec_available}))

    picks: list[dict] = []
    notes = ""
    if not merged:
        events.append(("done", {"total_picks": 0, "notes": "no candidate repos found"}))
    else:
        repos = _load_repos(merged, path)
        top = _structural_rerank(repos, intent)
        if not top:
            events.append(("done", {"total_picks": 0, "notes": "no usable candidates after rerank"}))
        else:
            for item in _compose_stack_stream(intent, top, ai_client):
                if item.get("__final"):
                    notes = item.get("notes", "") or ""
                    events.append(("done", {"total_picks": item.get("total_picks", 0), "notes": notes}))
                    break
                picks.append(item)
                events.append(("pick", item))

    try:
        _cache_set(qhash, query, events, path)
    except Exception as e:  # noqa: BLE001
        logger.warning("cache write failed: %s", e)

    return {
        "query": query,
        "intent": intent,
        "picks": picks,
        "degraded": not vec_available,
        "notes": notes,
        "cached": False,
        "error": None,
    }


# ---------- endpoint ----------

@router.post("/api/build")
def build(req: BuildRequest):
    query = (req.query or "").strip()
    if not query:
        return JSONResponse(status_code=400, content={"error": "query is required"})

    path = _db_path()
    qhash = _hash_query(query)

    cached = _cache_get(qhash, path)
    if cached is not None:
        def replay():
            yield sse("cache", {"hit": True})
            for event, data in cached:
                yield sse(event, data)
        return StreamingResponse(replay(), media_type="text/event-stream")

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    def generate():
        events: list[tuple[str, dict]] = []

        def emit(event: str, data: dict) -> str:
            events.append((event, data))
            return sse(event, data)

        if not api_key:
            yield emit("error", {"message": "ANTHROPIC_API_KEY not configured"})
            return

        try:
            ai_client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:  # noqa: BLE001
            yield emit("error", {"message": f"anthropic client init failed: {e}"})
            return

        # 1. intent
        intent = _extract_intent(query, ai_client)
        yield emit("intent", intent)

        # 2. retrieval
        vec_query_text = query + " " + " ".join(intent.get("capabilities", []))
        vec_hits = _vec_search(vec_query_text, path)
        fts_ids = _fts_candidates(query, path)

        vec_available = bool(vec_hits)
        if not vec_available:
            yield emit("degraded", {"degraded": True, "reason": "vector_search_unavailable"})

        merged = _rrf_merge([v[0] for v in vec_hits], fts_ids)
        if not merged and fts_ids:
            merged = fts_ids[:CANDIDATE_LIMIT]

        yield emit("candidates", {"repo_ids": merged, "degraded": not vec_available})

        if not merged:
            yield emit("done", {"total_picks": 0, "notes": "no candidate repos found"})
            _cache_set(qhash, query, events, path)
            return

        # 3. rerank
        repos = _load_repos(merged, path)
        top = _structural_rerank(repos, intent)

        if not top:
            yield emit("done", {"total_picks": 0, "notes": "no usable candidates after rerank"})
            _cache_set(qhash, query, events, path)
            return

        # 4. stack composition (streaming)
        total_picks = 0
        notes = ""
        for item in _compose_stack_stream(intent, top, ai_client):
            if item.get("__final"):
                total_picks = item.get("total_picks", 0)
                notes = item.get("notes", "")
                break
            yield emit("pick", item)

        yield emit("done", {"total_picks": total_picks, "notes": notes})

        # 5. cache write
        try:
            _cache_set(qhash, query, events, path)
        except Exception as e:  # noqa: BLE001
            logger.warning("cache write failed: %s", e)

    return StreamingResponse(generate(), media_type="text/event-stream")
