"""Tests for src.api.build — POST /api/build SSE endpoint."""
from __future__ import annotations

import json
import os
import struct
import tempfile
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

from src import embeddings as emb_mod
from src.db import init_db, insert_repo, _connect
from src.search import init_fts


# ----- Fake Anthropic client -----

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
        self.parent.create_calls.append({"model": model, "messages": messages})
        # Haiku intent extraction — return JSON
        intent = {
            "capabilities": ["vector search", "rag"],
            "constraints": ["local-only"],
            "language": "python",
            "scale": "small",
        }
        return _FakeMsgResp(json.dumps(intent))

    def stream(self, *, model, max_tokens, system, messages):
        self.parent.stream_calls.append({"model": model, "system": system})
        # Stream a few picks + a notes line. Must match a valid repo_id.
        picks = self.parent.stream_picks
        chunks: list[str] = []
        for p in picks:
            chunks.append(json.dumps(p) + "\n")
        chunks.append(json.dumps({"notes": "balanced stack"}) + "\n")
        return _FakeStreamCtx(chunks)


class FakeAnthropic:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.create_calls: list[dict] = []
        self.stream_calls: list[dict] = []
        self.stream_picks: list[dict] = []
        self.messages = _FakeMessages(self)


# ----- Fixtures -----

@pytest.fixture
def db_path(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    repos = [
        {"github_id": 1, "owner": "a", "name": "chroma", "full_name": "a/chroma",
         "description": "Open-source embedding vector database for RAG",
         "stars": 10000, "topics": ["vector-database", "rag", "embeddings"],
         "language": "Python", "category_primary": "infrastructure",
         "readme_excerpt": "Chroma is an AI-native open-source vector database.",
         "reepo_score": 85, "updated_at": "2025-01-01T00:00:00Z"},
        {"github_id": 2, "owner": "b", "name": "langchain", "full_name": "b/langchain",
         "description": "Framework for building LLM applications with RAG pipelines",
         "stars": 80000, "topics": ["llm", "rag", "framework"],
         "language": "Python", "category_primary": "frameworks",
         "readme_excerpt": "Build context-aware LLM apps with composable chains.",
         "reepo_score": 90, "updated_at": "2025-02-01T00:00:00Z"},
        {"github_id": 3, "owner": "c", "name": "ollama", "full_name": "c/ollama",
         "description": "Run large language models locally",
         "stars": 50000, "topics": ["llm", "local", "inference"],
         "language": "Go", "category_primary": "apps",
         "readme_excerpt": "Run Llama and Mistral models locally.",
         "reepo_score": 80, "updated_at": "2025-03-01T00:00:00Z"},
        {"github_id": 4, "owner": "d", "name": "fastapi", "full_name": "d/fastapi",
         "description": "Modern fast web framework for APIs",
         "stars": 70000, "topics": ["api", "python", "web"],
         "language": "Python", "category_primary": "frameworks",
         "readme_excerpt": "FastAPI is a modern Python web framework.",
         "reepo_score": 88, "updated_at": "2025-01-15T00:00:00Z"},
    ]
    ids = [insert_repo(r, path) for r in repos]
    # Add use_cases column so init_fts's SELECT succeeds.
    conn = _connect(path)
    conn.execute("ALTER TABLE repos ADD COLUMN use_cases TEXT")
    conn.commit()
    conn.close()
    init_fts(path)

    # Seed in-memory repo id list for tests that need it.
    monkeypatch.setenv("REEPO_DB_PATH", path)
    yield path, ids
    os.unlink(path)


@pytest.fixture
def app_client(db_path, monkeypatch):
    path, ids = db_path
    # Force no VOYAGE key by default — tests enable as needed.
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    from src import server as server_mod
    # Rebuild app with our db path
    app = server_mod.create_app(db_path=path)
    client = TestClient(app)
    return client, path, ids


def _parse_sse(body: bytes) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in body.decode("utf-8").split("\n\n"):
        if not block.strip():
            continue
        event = None
        data = None
        for line in block.split("\n"):
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        if event is not None and data is not None:
            events.append((event, data))
    return events


def _install_fake_anthropic(monkeypatch, picks: list[dict]):
    import src.api.build as build_mod
    fake_holder: dict = {}

    def _factory(api_key=None):
        c = FakeAnthropic(api_key=api_key)
        c.stream_picks = picks
        fake_holder["client"] = c
        return c

    monkeypatch.setattr(build_mod.anthropic, "Anthropic", _factory)
    return fake_holder


# ----- Tests -----

def test_empty_query_returns_400(app_client):
    client, _, _ = app_client
    r = client.post("/api/build", json={"query": ""})
    assert r.status_code == 400


def test_successful_flow_fts_only(app_client, monkeypatch):
    client, path, ids = app_client
    picks = [
        {"repo_id": ids[0], "role": "vector store", "why": "embedding db for rag"},
        {"repo_id": ids[1], "role": "agent framework", "why": "composable llm chains"},
    ]
    _install_fake_anthropic(monkeypatch, picks)

    r = client.post("/api/build", json={"query": "rag framework"})
    assert r.status_code == 200
    events = _parse_sse(r.content)
    names = [e[0] for e in events]

    assert "intent" in names
    assert "candidates" in names
    assert names.count("pick") >= 1
    assert names[-1] == "done"
    # Order check
    assert names.index("intent") < names.index("candidates")
    assert names.index("candidates") < names.index("pick")
    # Degraded event present since VOYAGE_API_KEY missing
    assert "degraded" in names


def test_cache_hit_on_second_call(app_client, monkeypatch):
    client, path, ids = app_client
    picks = [
        {"repo_id": ids[0], "role": "vector store", "why": "rag store"},
    ]
    holder = _install_fake_anthropic(monkeypatch, picks)

    q = "rag"
    r1 = client.post("/api/build", json={"query": q})
    assert r1.status_code == 200
    first_create_calls = len(holder["client"].create_calls)
    first_stream_calls = len(holder["client"].stream_calls)
    assert first_create_calls >= 1
    assert first_stream_calls >= 1

    # Second call — should replay from cache, no new anthropic calls.
    holder2 = _install_fake_anthropic(monkeypatch, picks)
    r2 = client.post("/api/build", json={"query": q})
    assert r2.status_code == 200
    events2 = _parse_sse(r2.content)
    names2 = [e[0] for e in events2]
    assert names2[0] == "cache"
    assert "pick" in names2
    assert "done" in names2
    # Fresh fake was installed but never called since cache served response
    assert "client" not in holder2 or (
        len(holder2["client"].create_calls) == 0 and len(holder2["client"].stream_calls) == 0
    )


def test_graceful_degradation_no_voyage(app_client, monkeypatch):
    client, path, ids = app_client
    # VOYAGE_API_KEY already unset in fixture
    picks = [{"repo_id": ids[1], "role": "framework", "why": "rag support"}]
    _install_fake_anthropic(monkeypatch, picks)

    r = client.post("/api/build", json={"query": "rag"})
    assert r.status_code == 200
    events = _parse_sse(r.content)

    # Expect a degraded event OR candidates with degraded: true
    degraded_seen = any(
        (e[0] == "degraded" and e[1].get("degraded") is True)
        or (e[0] == "candidates" and e[1].get("degraded") is True)
        for e in events
    )
    assert degraded_seen
    # Should still produce at least one pick
    assert any(e[0] == "pick" for e in events)
    assert any(e[0] == "done" for e in events)


def test_vector_path_used_when_embeddings_exist(app_client, monkeypatch):
    client, path, ids = app_client
    monkeypatch.setenv("VOYAGE_API_KEY", "fake")

    # Seed repo_embeddings with fake 512-dim vectors
    dim = emb_mod.EMBEDDING_DIM
    conn = _connect(path)
    try:
        for i, rid in enumerate(ids):
            v = [0.0] * dim
            v[i % dim] = 1.0
            blob = struct.pack(f"{dim}f", *v)
            conn.execute(
                "INSERT INTO repo_embeddings(repo_id, embedding) VALUES (?, ?)",
                (rid, blob),
            )
        conn.commit()
    finally:
        conn.close()

    # Patch embed_query to return a deterministic vector
    def fake_embed_query(text: str) -> list[float]:
        v = [0.0] * dim
        v[0] = 1.0
        return v

    monkeypatch.setattr(emb_mod, "embed_query", fake_embed_query)

    picks = [{"repo_id": ids[0], "role": "vector db", "why": "because"}]
    _install_fake_anthropic(monkeypatch, picks)

    r = client.post("/api/build", json={"query": "vector"})
    assert r.status_code == 200
    events = _parse_sse(r.content)
    names = [e[0] for e in events]
    # Not degraded
    cand_events = [e for e in events if e[0] == "candidates"]
    assert cand_events
    assert cand_events[0][1].get("degraded") is False
    assert "pick" in names
