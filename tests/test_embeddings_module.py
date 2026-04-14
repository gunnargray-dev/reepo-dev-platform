"""Tests for src.embeddings — Voyage client wrapper."""
from __future__ import annotations

import pytest

from src import embeddings


class _FakeResponse:
    def __init__(self, n: int):
        self.embeddings = [[0.0] * embeddings.EMBEDDING_DIM for _ in range(n)]


class _FakeClient:
    def __init__(self):
        self.calls: list[dict] = []

    def embed(self, texts, model, input_type):
        self.calls.append({"texts": list(texts), "model": model, "input_type": input_type})
        return _FakeResponse(len(texts))


@pytest.fixture(autouse=True)
def _reset_client():
    embeddings._reset_client_for_tests()
    yield
    embeddings._reset_client_for_tests()


def test_embed_texts_raises_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="VOYAGE_API_KEY not set"):
        embeddings.embed_texts(["hello"])


def test_embed_query_raises_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="VOYAGE_API_KEY not set"):
        embeddings.embed_query("hello")


def test_embed_texts_batches_at_most_128(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(embeddings, "_client", fake)

    texts = [f"doc {i}" for i in range(300)]
    out = embeddings.embed_texts(texts)

    assert len(out) == 300
    # Three batches: 128, 128, 44
    batch_sizes = [len(c["texts"]) for c in fake.calls]
    assert batch_sizes == [128, 128, 44]
    assert all(sz <= 128 for sz in batch_sizes)
    assert all(c["input_type"] == "document" for c in fake.calls)
    assert all(c["model"] == embeddings.EMBEDDING_MODEL for c in fake.calls)


def test_embed_query_uses_query_input_type(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(embeddings, "_client", fake)

    vec = embeddings.embed_query("find me a react chart lib")

    assert len(fake.calls) == 1
    assert fake.calls[0]["input_type"] == "query"
    assert fake.calls[0]["texts"] == ["find me a react chart lib"]
    assert len(vec) == embeddings.EMBEDDING_DIM


def test_embed_texts_empty_returns_empty(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(embeddings, "_client", fake)
    assert embeddings.embed_texts([]) == []
    assert fake.calls == []


def test_module_constants():
    assert embeddings.EMBEDDING_MODEL == "voyage-3-lite"
    assert embeddings.EMBEDDING_DIM == 512
    assert embeddings.EMBEDDING_VERSION == 1
