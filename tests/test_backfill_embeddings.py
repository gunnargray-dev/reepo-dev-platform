"""Tests for scripts/backfill_embeddings.py."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts import backfill_embeddings as bf
from src import db as db_module
from src import embeddings as embeddings_module


def _make_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "test.db")
    db_module.init_db(db_path)
    return db_path


def _insert(
    db_path: str,
    *,
    github_id: int,
    full_name: str,
    description: str | None = "desc",
    readme: str | None = "readme",
    topics: list[str] | None = None,
) -> int:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO repos (github_id, owner, name, full_name, description, "
            "readme_excerpt, topics) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                github_id,
                full_name.split("/")[0],
                full_name.split("/")[1],
                full_name,
                description,
                readme,
                json.dumps(topics or []),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _fake_embed_factory(call_log: list[list[str]]):
    def _fake(texts):
        call_log.append(list(texts))
        return [[float(i)] * embeddings_module.EMBEDDING_DIM for i in range(len(texts))]
    return _fake


def test_dry_run_makes_no_api_calls_and_writes_nothing(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    _insert(db_path, github_id=1, full_name="a/b")
    _insert(db_path, github_id=2, full_name="c/d")

    calls: list[list[str]] = []
    monkeypatch.setattr(embeddings_module, "embed_texts", _fake_embed_factory(calls))

    summary = bf.run(db_path=db_path, limit=None, batch_size=10, reembed=False, dry_run=True)

    assert calls == []
    assert summary["processed"] == 2
    assert summary["dry_run"] is True

    conn = db_module._connect(db_path)
    try:
        rows = conn.execute(
            "SELECT embedding_version FROM repos ORDER BY id"
        ).fetchall()
        assert [r[0] for r in rows] == [None, None]
        n = conn.execute("SELECT COUNT(*) FROM repo_embeddings").fetchone()[0]
        assert n == 0
    finally:
        conn.close()


def test_normal_run_sets_version_and_inserts_embeddings(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    id1 = _insert(db_path, github_id=1, full_name="a/b")
    id2 = _insert(db_path, github_id=2, full_name="c/d")

    calls: list[list[str]] = []
    monkeypatch.setattr(embeddings_module, "embed_texts", _fake_embed_factory(calls))

    summary = bf.run(db_path=db_path, limit=None, batch_size=10, reembed=False, dry_run=False)
    assert summary["processed"] == 2
    assert summary["failed"] == 0
    assert len(calls) == 1

    conn = db_module._connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, embedding_version, embedded_at FROM repos ORDER BY id"
        ).fetchall()
        assert [r[1] for r in rows] == [embeddings_module.EMBEDDING_VERSION] * 2
        assert all(r[2] for r in rows)
        n = conn.execute("SELECT COUNT(*) FROM repo_embeddings").fetchone()[0]
        assert n == 2
        ids = {r[0] for r in conn.execute("SELECT repo_id FROM repo_embeddings").fetchall()}
        assert ids == {id1, id2}
    finally:
        conn.close()


def test_second_run_is_noop(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    _insert(db_path, github_id=1, full_name="a/b")

    calls: list[list[str]] = []
    monkeypatch.setattr(embeddings_module, "embed_texts", _fake_embed_factory(calls))

    bf.run(db_path=db_path, limit=None, batch_size=10, reembed=False, dry_run=False)
    assert len(calls) == 1

    summary = bf.run(db_path=db_path, limit=None, batch_size=10, reembed=False, dry_run=False)
    assert len(calls) == 1  # no new calls
    assert summary["processed"] == 0
    assert summary["selected"] == 0


def test_limit_respected(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    for i in range(5):
        _insert(db_path, github_id=i + 1, full_name=f"o/r{i}")

    calls: list[list[str]] = []
    monkeypatch.setattr(embeddings_module, "embed_texts", _fake_embed_factory(calls))

    summary = bf.run(db_path=db_path, limit=2, batch_size=10, reembed=False, dry_run=False)
    assert summary["selected"] == 2
    assert summary["processed"] == 2
    assert len(calls[0]) == 2

    conn = db_module._connect(db_path)
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM repos WHERE embedding_version IS NOT NULL"
        ).fetchone()[0]
        assert n == 2
    finally:
        conn.close()


def test_empty_source_repo_skipped(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    empty_id = _insert(db_path, github_id=1, full_name="a/b", description=None, readme=None)
    good_id = _insert(db_path, github_id=2, full_name="c/d")

    calls: list[list[str]] = []
    monkeypatch.setattr(embeddings_module, "embed_texts", _fake_embed_factory(calls))

    summary = bf.run(db_path=db_path, limit=None, batch_size=10, reembed=False, dry_run=False)
    assert summary["skipped_empty"] == 1
    assert summary["processed"] == 1
    # Only one text embedded (the good one)
    assert len(calls) == 1 and len(calls[0]) == 1

    conn = db_module._connect(db_path)
    try:
        row = conn.execute(
            "SELECT embedding_version FROM repos WHERE id = ?", (empty_id,)
        ).fetchone()
        assert row[0] is None
        present = conn.execute(
            "SELECT COUNT(*) FROM repo_embeddings WHERE repo_id = ?", (empty_id,)
        ).fetchone()[0]
        assert present == 0

        good_row = conn.execute(
            "SELECT embedding_version FROM repos WHERE id = ?", (good_id,)
        ).fetchone()
        assert good_row[0] == embeddings_module.EMBEDDING_VERSION
    finally:
        conn.close()


def test_failure_marks_sentinel_and_continues(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    # 3 repos; with batch_size=1 we get three independent batches.
    ids = [_insert(db_path, github_id=i + 1, full_name=f"o/r{i}") for i in range(3)]

    call_count = {"n": 0}

    def flaky(texts):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("boom")
        return [[0.1] * embeddings_module.EMBEDDING_DIM for _ in texts]

    monkeypatch.setattr(embeddings_module, "embed_texts", flaky)

    summary = bf.run(db_path=db_path, limit=None, batch_size=1, reembed=False, dry_run=False)
    assert summary["failed"] == 1
    assert summary["processed"] == 2

    conn = db_module._connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, embedding_version FROM repos ORDER BY id"
        ).fetchall()
        versions = {r[0]: r[1] for r in rows}
        # First and third processed OK; second batch failed.
        assert versions[ids[0]] == embeddings_module.EMBEDDING_VERSION
        assert versions[ids[1]] == bf.FAILURE_SENTINEL
        assert versions[ids[2]] == embeddings_module.EMBEDDING_VERSION

        # Sentinel row should not be picked up on a subsequent run.
        candidates = bf._select_candidates(conn, reembed=False, limit=None)
        assert all(c["id"] != ids[1] for c in candidates)
    finally:
        conn.close()


def test_document_truncation(tmp_path):
    long_desc = "x" * 10_000
    row = {
        "description": long_desc,
        "topics": json.dumps(["ai", "ml"]),
        "readme_excerpt": "readme body",
    }
    doc = bf._build_document(row)
    assert len(doc) == bf.MAX_DOC_CHARS
