"""Backfill `repo_embeddings` for repos missing up-to-date vectors.

Resumable, crash-safe (commit per batch), idempotent across runs. Uses
`src.embeddings.embed_texts` for the Voyage API and `src.db._connect` so the
sqlite-vec extension is loaded on the connection.

Usage:
    python scripts/backfill_embeddings.py [--limit N] [--batch-size N]
        [--db PATH] [--reembed] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone

import sqlite_vec

# Allow running as a script (`python scripts/backfill_embeddings.py`) by
# ensuring the project root is on sys.path.
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src import db as db_module  # noqa: E402
from src import embeddings as embeddings_module  # noqa: E402

logger = logging.getLogger("backfill_embeddings")

MAX_DOC_CHARS = 4000
FAILURE_SENTINEL = -1


def _build_document(row: dict) -> str:
    """Combine text fields into a single embedding document. May return ''."""
    parts: list[str] = []
    desc = row.get("description")
    if desc:
        parts.append(str(desc).strip())

    topics_raw = row.get("topics")
    if topics_raw:
        try:
            topics = json.loads(topics_raw) if isinstance(topics_raw, str) else topics_raw
        except (json.JSONDecodeError, TypeError):
            topics = []
        if topics:
            parts.append("Topics: " + ", ".join(str(t) for t in topics))

    use_cases_raw = row.get("use_cases") if "use_cases" in row.keys() else None
    if use_cases_raw:
        try:
            use_cases = (
                json.loads(use_cases_raw) if isinstance(use_cases_raw, str) else use_cases_raw
            )
        except (json.JSONDecodeError, TypeError):
            use_cases = []
        if use_cases:
            parts.append("Use cases: " + ", ".join(str(u) for u in use_cases))

    readme = row.get("readme_excerpt")
    if readme:
        parts.append(str(readme).strip())

    doc = "\n\n".join(p for p in parts if p)
    if len(doc) > MAX_DOC_CHARS:
        doc = doc[:MAX_DOC_CHARS]
    return doc


def _has_source_text(row: dict) -> bool:
    desc = (row.get("description") or "").strip()
    readme = (row.get("readme_excerpt") or "").strip()
    return bool(desc or readme)


def _table_has_column(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
    return any(r[1] == column for r in rows)


def _select_candidates(conn, reembed: bool, limit: int | None) -> list[dict]:
    if reembed:
        where = ""
        params: tuple = ()
    else:
        where = (
            "WHERE embedding_version IS NULL "
            "OR (embedding_version != ? AND embedding_version != ?)"
        )
        # Exclude rows already at current version AND rows marked failed
        # (sentinel = -1). We explicitly skip the sentinel so the script does
        # not infinitely retry broken repos.
        params = (embeddings_module.EMBEDDING_VERSION, FAILURE_SENTINEL)
    query = f"SELECT * FROM repos {where} ORDER BY id ASC"
    if limit is not None:
        query += f" LIMIT {int(limit)}"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _process_batch(
    conn,
    batch: list[dict],
    dry_run: bool,
) -> tuple[int, int]:
    """Embed + write one batch. Returns (processed, failed)."""
    docs = [_build_document(r) for r in batch]
    ids = [r["id"] for r in batch]

    if dry_run:
        logger.info(
            "[dry-run] would embed %d repos (ids=%s)",
            len(batch),
            ids[:5] + (["..."] if len(ids) > 5 else []),
        )
        return len(batch), 0

    try:
        vectors = embeddings_module.embed_texts(docs)
    except Exception as e:  # noqa: BLE001
        logger.error(
            "embedding batch failed (ids=%s): %s — marking sentinel", ids, e
        )
        now = _now_iso()
        for rid in ids:
            conn.execute(
                "UPDATE repos SET embedding_version = ?, embedded_at = ? WHERE id = ?",
                (FAILURE_SENTINEL, now, rid),
            )
        conn.commit()
        return 0, len(batch)

    if len(vectors) != len(batch):
        raise RuntimeError(
            f"embed_texts returned {len(vectors)} vectors for {len(batch)} inputs"
        )

    now = _now_iso()
    for rid, vec in zip(ids, vectors):
        conn.execute(
            "INSERT OR REPLACE INTO repo_embeddings(repo_id, embedding) VALUES (?, ?)",
            (rid, sqlite_vec.serialize_float32(vec)),
        )
        conn.execute(
            "UPDATE repos SET embedding_version = ?, embedded_at = ? WHERE id = ?",
            (embeddings_module.EMBEDDING_VERSION, now, rid),
        )
    conn.commit()
    return len(batch), 0


def run(
    db_path: str,
    limit: int | None,
    batch_size: int,
    reembed: bool,
    dry_run: bool,
) -> dict:
    """Execute the backfill. Returns a summary dict."""
    t_start = time.monotonic()

    # Ensure schema (adds embedding columns/vec0 table if missing).
    db_module.init_db(db_path)

    conn = db_module._connect(db_path)
    try:
        has_use_cases = _table_has_column(conn, "repos", "use_cases")
        if not has_use_cases:
            logger.debug("repos.use_cases column not present — skipping that field")

        candidates = _select_candidates(conn, reembed=reembed, limit=limit)
        total = len(candidates)
        logger.info("selected %d repo(s) for embedding backfill", total)

        processed = 0
        skipped = 0
        failed = 0

        # Filter + batch
        eligible: list[dict] = []
        for row in candidates:
            if not _has_source_text(row):
                skipped += 1
                logger.info(
                    "skip repo id=%s (%s): empty description and readme_excerpt",
                    row.get("id"),
                    row.get("full_name"),
                )
                continue
            eligible.append(row)

        for i in range(0, len(eligible), batch_size):
            batch = eligible[i : i + batch_size]
            t_batch = time.monotonic()
            p, f = _process_batch(conn, batch, dry_run=dry_run)
            processed += p
            failed += f
            done = min(i + batch_size, len(eligible))
            logger.info(
                "[%d/%d] processed batch in %.2fs (ok=%d fail=%d)",
                done,
                len(eligible),
                time.monotonic() - t_batch,
                p,
                f,
            )

        elapsed = time.monotonic() - t_start
        summary = {
            "selected": total,
            "processed": processed,
            "skipped_empty": skipped,
            "failed": failed,
            "elapsed_seconds": round(elapsed, 2),
            "dry_run": dry_run,
        }
        logger.info("backfill summary: %s", summary)
        return summary
    finally:
        conn.close()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill repo embeddings.")
    p.add_argument("--limit", type=int, default=None, help="Max repos this run.")
    p.add_argument("--batch-size", type=int, default=128, help="Embedding API batch size.")
    p.add_argument(
        "--db",
        type=str,
        default=db_module.DEFAULT_DB_PATH,
        help="SQLite DB path.",
    )
    p.add_argument("--reembed", action="store_true", help="Re-embed all repos.")
    p.add_argument("--dry-run", action="store_true", help="No API calls, no writes.")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not args.dry_run and not os.environ.get("VOYAGE_API_KEY"):
        logger.error("VOYAGE_API_KEY not set; aborting. Use --dry-run to preview.")
        return 2

    try:
        run(
            db_path=args.db,
            limit=args.limit,
            batch_size=args.batch_size,
            reembed=args.reembed,
            dry_run=args.dry_run,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("fatal error: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
