"""Tests for GET /api/search NL routing (mode=keyword|ai|auto)."""
from __future__ import annotations

import json
import os
import tempfile
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

from src.db import init_db, insert_repo, _connect
from src.search import init_fts


# ---------- fake anthropic ----------

class _FakeTextStream:
    def __init__(self, chunks: Iterable[str]):
        self._chunks = list(chunks)

    def __iter__(self):
        for c in self._chunks:
            yield c


class _FakeStreamCtx:
    def __init__(self, chunks: Iterable[str]):
        self.text_stream = _FakeTextStream(chunks)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _FakeMsgContent:
    def __init__(self, text: str):
        self.text = text


class _FakeMsgResp:
    def __init__(self, text: str):
        self.content = [_FakeMsgContent(text)]


class _FakeMessages:
    def __init__(self, parent):
        self.parent = parent

    def create(self, *, model, max_tokens, messages, system=None):
        self.parent.create_calls.append({"model": model})
        intent = {
            "capabilities": ["rag", "vector search"],
            "constraints": [],
            "language": "python",
            "scale": "small",
        }
        return _FakeMsgResp(json.dumps(intent))

    def stream(self, *, model, max_tokens, system, messages):
        self.parent.stream_calls.append({"model": model})
        chunks = []
        for p in self.parent.stream_picks:
            chunks.append(json.dumps(p) + "\n")
        chunks.append(json.dumps({"notes": "ok"}) + "\n")
        return _FakeStreamCtx(chunks)


class FakeAnthropic:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.create_calls: list[dict] = []
        self.stream_calls: list[dict] = []
        self.stream_picks: list[dict] = []
        self.messages = _FakeMessages(self)


# ---------- fixtures ----------

@pytest.fixture
def app_client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    repos = [
        {"github_id": 1, "owner": "a", "name": "chroma", "full_name": "a/chroma",
         "description": "Open-source embedding vector database for RAG",
         "stars": 10000, "topics": ["vector-database", "rag"],
         "language": "Python", "category_primary": "infrastructure",
         "readme_excerpt": "Vector db.", "reepo_score": 85,
         "updated_at": "2025-01-01T00:00:00Z"},
        {"github_id": 2, "owner": "b", "name": "langchain", "full_name": "b/langchain",
         "description": "Framework I want to build a local RAG app with for LLM apps with RAG pipelines",
         "stars": 80000, "topics": ["llm", "rag"],
         "language": "Python", "category_primary": "frameworks",
         "readme_excerpt": "I want to build a local RAG app langchain.",
         "reepo_score": 90, "updated_at": "2025-02-01T00:00:00Z"},
        {"github_id": 3, "owner": "tiangolo", "name": "fastapi",
         "full_name": "tiangolo/fastapi",
         "description": "Modern fast web framework for building APIs",
         "stars": 70000, "topics": ["api", "python"],
         "language": "Python", "category_primary": "frameworks",
         "readme_excerpt": "FastAPI.", "reepo_score": 88,
         "updated_at": "2025-01-15T00:00:00Z"},
        {"github_id": 4, "owner": "q", "name": "qdrant", "full_name": "q/qdrant",
         "description": "Vector database for similarity search",
         "stars": 20000, "topics": ["vector", "rust"],
         "language": "Rust", "category_primary": "infrastructure",
         "readme_excerpt": "Qdrant.", "reepo_score": 82,
         "updated_at": "2025-01-20T00:00:00Z"},
    ]
    ids = [insert_repo(r, path) for r in repos]
    conn = _connect(path)
    conn.execute("ALTER TABLE repos ADD COLUMN use_cases TEXT")
    conn.commit()
    conn.close()
    init_fts(path)

    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    # Clear in-memory search cache between tests
    from src.middleware import search_cache
    if hasattr(search_cache, "_cache"):
        search_cache._cache.clear()

    from src import server as server_mod
    app = server_mod.create_app(db_path=path)
    client = TestClient(app)

    yield client, path, ids
    os.unlink(path)


def _install_fake_anthropic(monkeypatch, picks):
    import src.api.build as build_mod
    holder: dict = {}

    def factory(api_key=None):
        c = FakeAnthropic(api_key=api_key)
        c.stream_picks = picks
        holder["client"] = c
        return c

    monkeypatch.setattr(build_mod.anthropic, "Anthropic", factory)
    return holder


# ---------- tests ----------

def test_keyword_default_no_anthropic_call(app_client, monkeypatch):
    client, _, _ = app_client
    holder = _install_fake_anthropic(monkeypatch, [])

    r = client.get("/api/search", params={"q": "fastapi"})
    assert r.status_code == 200
    data = r.json()
    assert data["mode"] == "keyword"
    assert "results" in data
    assert "total" in data
    assert "client" not in holder  # anthropic constructor never invoked


def test_mode_ai_routes_through_pipeline(app_client, monkeypatch):
    client, _, ids = app_client
    picks = [{"repo_id": ids[0], "role": "vector store", "why": "rag"}]
    holder = _install_fake_anthropic(monkeypatch, picks)

    r = client.get("/api/search", params={"q": "rag", "mode": "ai"})
    assert r.status_code == 200
    data = r.json()
    assert data["mode"] == "ai"
    assert isinstance(data["picks"], list)
    assert len(data["picks"]) >= 1
    pick = data["picks"][0]
    # Enrichment fields
    assert pick["id"] == ids[0]
    assert pick["full_name"] == "a/chroma"
    assert pick["owner"] == "a"
    assert pick["name"] == "chroma"
    assert "stars" in pick and "reepo_score" in pick and "language" in pick
    # Anthropic was called
    assert "client" in holder
    assert len(holder["client"].create_calls) >= 1
    assert len(holder["client"].stream_calls) >= 1


def test_mode_auto_nl_query_routes_to_ai(app_client, monkeypatch):
    client, _, ids = app_client
    picks = [{"repo_id": ids[1], "role": "framework", "why": "rag pipelines"}]
    holder = _install_fake_anthropic(monkeypatch, picks)

    r = client.get(
        "/api/search",
        params={"q": "I want to build a local RAG app", "mode": "auto"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["mode"] == "ai"
    assert len(data["picks"]) >= 1
    assert "client" in holder


def test_mode_auto_keyword_query_stays_keyword(app_client, monkeypatch):
    client, _, _ = app_client
    holder = _install_fake_anthropic(monkeypatch, [])

    r = client.get("/api/search", params={"q": "qdrant", "mode": "auto"})
    assert r.status_code == 200
    data = r.json()
    assert data["mode"] == "keyword"
    assert "results" in data
    assert "client" not in holder


def test_empty_query_auto_mode_returns_400_when_routed_ai(app_client, monkeypatch):
    """Empty query with auto mode should classify as keyword (empty -> not NL)
    and the keyword path returns an empty result, not 400. But empty + mode=ai
    should 400."""
    client, _, _ = app_client
    _install_fake_anthropic(monkeypatch, [])

    # mode=ai explicitly with empty -> 400
    r = client.get("/api/search", params={"q": "", "mode": "ai"})
    assert r.status_code == 400


def test_empty_query_auto_returns_empty_keyword(app_client, monkeypatch):
    client, _, _ = app_client
    _install_fake_anthropic(monkeypatch, [])
    r = client.get("/api/search", params={"q": "", "mode": "auto"})
    # Empty is not NL -> keyword. Existing behavior allowed empty q.
    assert r.status_code == 200
    assert r.json()["mode"] == "keyword"


def test_ai_cache_dedups_anthropic_calls(app_client, monkeypatch):
    client, _, ids = app_client
    picks = [{"repo_id": ids[1], "role": "framework", "why": "rag pipelines"}]
    holder = _install_fake_anthropic(monkeypatch, picks)

    q = "build rag"
    r1 = client.get("/api/search", params={"q": q, "mode": "ai"})
    assert r1.status_code == 200
    first_creates = len(holder["client"].create_calls)
    first_streams = len(holder["client"].stream_calls)
    assert first_creates >= 1 and first_streams >= 1

    # Reinstall fake to detect any new calls; clear in-memory search cache so
    # we exercise the ai_query_cache layer (not just the per-process LRU).
    from src.middleware import search_cache
    if hasattr(search_cache, "_cache"):
        search_cache._cache.clear()

    holder2 = _install_fake_anthropic(monkeypatch, picks)
    r2 = client.get("/api/search", params={"q": q, "mode": "ai"})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["mode"] == "ai"
    assert len(data2["picks"]) >= 1
    # Cache should serve — no new anthropic calls.
    if "client" in holder2:
        assert len(holder2["client"].create_calls) == 0
        assert len(holder2["client"].stream_calls) == 0


def test_invalid_mode_returns_400(app_client):
    client, _, _ = app_client
    r = client.get("/api/search", params={"q": "fastapi", "mode": "bogus"})
    assert r.status_code == 400
