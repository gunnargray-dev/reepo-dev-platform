"""Regenerate repo summaries + use cases via headless Claude Code.

Uses the Max subscription (not API credits). Fetches raw READMEs (cached to
data/readmes/{id}.md), then calls `claude -p --json-schema` once per repo to
extract BOTH a short description summary and 3-4 concrete use cases.

Writes to repos.readme_excerpt (summary) and repos.use_cases (JSON array).

Usage:
    GITHUB_TOKEN=... .venv/bin/python scripts/extract_use_cases_claude.py
    GITHUB_TOKEN=... .venv/bin/python scripts/extract_use_cases_claude.py --limit 10
    GITHUB_TOKEN=... .venv/bin/python scripts/extract_use_cases_claude.py --redo-all

Resume-safe: commits per repo; re-running picks up where it left off.
"""
import argparse
import base64
import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "reepo.db"
README_CACHE = PROJECT_ROOT / "data" / "readmes"
README_CACHE.mkdir(parents=True, exist_ok=True)

MODEL = "sonnet"

SYSTEM_PROMPT = (
    "You are a technical writer extracting repo summaries and use cases from GitHub READMEs. "
    "You write like an engineer who has actually used the tool, not like marketing copy. "
    "You avoid generic phrasing ('powerful', 'comprehensive', 'state-of-the-art'), "
    "avoid filler verbs ('leverage', 'utilize', 'facilitate'), avoid meta words "
    "('ultimately', 'essentially', 'landscape'), and never restate the obvious "
    "('build AI apps with this AI library'). "
    "You return ONLY the requested JSON."
)

USER_PROMPT = """Repository: {full_name}
GitHub description: {description}

README:
{readme}

Produce two things for THIS repo:

(1) SUMMARY — 2-3 sentences describing what the project is and what specific problem it solves. Written like a developer describing the project to a colleague. No marketing language. No "is a comprehensive" or "powerful framework for". Don't start with the repo name. Name concrete technologies, algorithms, or outputs where relevant. Plain text, no markdown.

(2) USE CASES — 3-4 concrete things a developer could BUILD or DO with THIS specific repo. Each should let a reader decide "yes that's my problem" or "no not my problem". Requirements:
  - 10-18 words each
  - Start with an action verb (Build, Deploy, Train, Generate, Query, Stream, Index, etc.)
  - Name specific technologies, data types, or outputs mentioned in the README
  - No generic phrasing that could describe any repo in the category
  - Skip installation, licensing, contribution guidelines
  - For libraries: what the user builds WITH it, not what the library itself is
  - For apps: the problem the user solves by running it

Good summary example (vector DB):
  "An embedded vector database that stores and searches high-dimensional embeddings using HNSW indexes. Designed for applications where a full Postgres or Elasticsearch cluster is overkill, with zero-config persistence to a single file."

Bad summary example (AI slop):
  "A powerful, cutting-edge vector database solution that empowers developers to build state-of-the-art AI applications with unmatched performance."

Good use case example:
  "Index 10M+ document embeddings with HNSW for sub-millisecond semantic search"

Bad use case example:
  "Build powerful AI applications with cutting-edge vector search technology"

Return ONLY the JSON object."""

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "minLength": 60, "maxLength": 700},
        "use_cases": {
            "type": "array",
            "items": {"type": "string", "minLength": 20, "maxLength": 200},
            "minItems": 3,
            "maxItems": 4,
        },
    },
    "required": ["summary", "use_cases"],
    "additionalProperties": False,
}


def fetch_readme(owner: str, name: str, repo_id: int, gh_headers: dict) -> str | None:
    """Fetch raw README from GitHub (or disk cache). Returns None on failure."""
    cache = README_CACHE / f"{repo_id}.md"
    if cache.exists():
        text = cache.read_text(encoding="utf-8", errors="replace")
        return text if text.strip() else None

    try:
        resp = httpx.get(
            f"https://api.github.com/repos/{owner}/{name}/readme",
            headers=gh_headers,
            timeout=15.0,
            follow_redirects=True,
        )
    except Exception as e:
        print(f"  [gh-error] {owner}/{name}: {e}", file=sys.stderr)
        return None

    if resp.status_code != 200:
        # Cache the miss to avoid retrying on re-runs
        cache.write_text("", encoding="utf-8")
        return None

    try:
        content_b64 = resp.json().get("content", "")
        content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [decode-error] {owner}/{name}: {e}", file=sys.stderr)
        return None

    cache.write_text(content, encoding="utf-8")

    # Check rate limit
    remaining = int(resp.headers.get("X-RateLimit-Remaining", "100"))
    if remaining < 100:
        reset_at = int(resp.headers.get("X-RateLimit-Reset", "0"))
        wait = max(0, reset_at - int(time.time())) + 2
        if remaining < 10 and wait > 0:
            print(f"  [rate-limit] {remaining} left, sleeping {wait}s", file=sys.stderr)
            time.sleep(min(wait, 600))

    return content


TRANSIENT_MARKERS = ("500", "Internal server error", "Stream idle timeout", "overloaded", "rate_limit")


def _is_transient(text: str) -> bool:
    return any(m in text for m in TRANSIENT_MARKERS)


def call_claude(full_name: str, description: str, readme: str) -> dict | None:
    """Spawn `claude -p` to extract summary + use cases. Retries transient API errors."""
    readme_trunc = readme[:5000]
    if len(readme) > 5000:
        readme_trunc += "\n\n[...truncated]"
    user_prompt = USER_PROMPT.format(
        full_name=full_name,
        description=description or "(none)",
        readme=readme_trunc,
    )

    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    backoffs = [10, 30, 60]  # seconds between attempts 1->2, 2->3, 3->4

    for attempt in range(4):
        try:
            proc = subprocess.run(
                [
                    "claude",
                    "-p",
                    "--output-format", "json",
                    "--model", MODEL,
                    "--system-prompt", SYSTEM_PROMPT,
                    "--json-schema", json.dumps(SCHEMA),
                    "--disable-slash-commands",
                ],
                input=user_prompt,
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
                cwd="/tmp",
            )
        except subprocess.TimeoutExpired:
            print(f"  [timeout a={attempt}] {full_name}", file=sys.stderr)
            if attempt < 3:
                time.sleep(backoffs[attempt])
                continue
            return None
        except Exception as e:
            print(f"  [spawn-error] {full_name}: {e}", file=sys.stderr)
            return None

        # Parse stdout even on non-zero exit to detect transient API errors
        out = proc.stdout.strip()
        transient = False
        if proc.returncode != 0 or _is_transient(out[:600]):
            if _is_transient(out[:600]):
                transient = True
            else:
                err = proc.stderr.strip()[:200]
                print(f"  [exit={proc.returncode} a={attempt}] {full_name}: stderr={err!r} stdout={out[:300]!r}", file=sys.stderr)
                return None

        if transient:
            if attempt < 3:
                wait = backoffs[attempt]
                print(f"  [transient a={attempt}] {full_name}: retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  [transient-exhausted] {full_name}", file=sys.stderr)
            return None

        # Success path
        break

    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print(f"  [json-error] {full_name}: invalid stdout", file=sys.stderr)
        return None

    if result.get("is_error"):
        print(f"  [claude-error] {full_name}: {result.get('result', '')[:200]}", file=sys.stderr)
        return None

    structured = result.get("structured_output")
    if not isinstance(structured, dict):
        # Fall back to parsing `result` text in case schema wasn't respected
        text = result.get("result", "").strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text
            text = text.rsplit("```", 1)[0]
        try:
            structured = json.loads(text)
        except Exception:
            print(f"  [no-structured] {full_name}", file=sys.stderr)
            return None

    summary = structured.get("summary")
    cases = structured.get("use_cases")
    if not isinstance(summary, str) or len(summary) < 40:
        return None
    if not isinstance(cases, list) or not cases:
        return None
    return {
        "summary": summary.strip(),
        "use_cases": [str(c) for c in cases if isinstance(c, str) and len(c) >= 20],
    }


def process_one(row, gh_headers) -> tuple[str, str]:
    """Worker: fetch README + call Claude + update DB. Returns (status, full_name)."""
    repo_id = row["id"]
    full_name = row["full_name"]
    readme = fetch_readme(row["owner"], row["name"], repo_id, gh_headers)
    if not readme or len(readme) < 80:
        c = sqlite3.connect(DB_PATH, timeout=30)
        c.execute("UPDATE repos SET use_cases = ? WHERE id = ?", ("[]", repo_id))
        c.commit()
        c.close()
        return ("skipped", full_name)

    result = call_claude(full_name, row["description"] or "", readme)
    if result:
        c = sqlite3.connect(DB_PATH, timeout=30)
        c.execute(
            "UPDATE repos SET readme_excerpt = ?, use_cases = ? WHERE id = ?",
            (result["summary"], json.dumps(result["use_cases"]), repo_id),
        )
        c.commit()
        c.close()
        return ("ok", full_name)
    return ("failed", full_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Process at most N repos (0 = all)")
    parser.add_argument("--redo-all", action="store_true", help="Re-extract even if use_cases is set")
    parser.add_argument("--min-stars", type=int, default=0, help="Only process repos with stars >= N")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent Claude subprocesses")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise SystemExit("GITHUB_TOKEN env var is required")

    gh_headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}",
    }

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    where = []
    if not args.redo_all:
        # Missing either summary or use_cases
        where.append(
            "(use_cases IS NULL OR use_cases = '[]' "
            "OR readme_excerpt IS NULL OR length(readme_excerpt) < 60)"
        )
    if args.min_stars > 0:
        where.append(f"stars >= {args.min_stars}")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    rows = conn.execute(
        f"SELECT id, owner, name, full_name, description, stars "
        f"FROM repos {where_sql} ORDER BY stars DESC"
    ).fetchall()
    conn.close()

    if args.limit:
        rows = rows[: args.limit]

    total = len(rows)
    print(
        f"Processing {total} repos with Claude Code ({MODEL}) via Max subscription "
        f"[workers={args.workers}]",
        flush=True,
    )
    if total == 0:
        return

    # Enable WAL so concurrent writes from worker threads don't contend
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()

    start = time.time()
    counts = {"ok": 0, "skipped": 0, "failed": 0}
    counts_lock = threading.Lock()
    done = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process_one, row, gh_headers): row for row in rows}
        for fut in as_completed(futures):
            try:
                status, _name = fut.result()
            except Exception as e:
                row = futures[fut]
                print(f"  [worker-error] {row['full_name']}: {e}", file=sys.stderr)
                status = "failed"
            with counts_lock:
                counts[status] += 1
                done += 1
                cur_done = done
                cur_ok = counts["ok"]
                cur_skip = counts["skipped"]
                cur_fail = counts["failed"]
            if cur_done % 10 == 0 or cur_done == total:
                elapsed = time.time() - start
                rate = cur_done / elapsed if elapsed > 0 else 0
                eta_h = ((total - cur_done) / rate / 3600) if rate > 0 else 0
                print(
                    f"[{cur_done}/{total}] ok={cur_ok} skipped={cur_skip} failed={cur_fail} "
                    f"rate={rate:.2f}/s eta={eta_h:.1f}h",
                    flush=True,
                )

    print(f"Done: ok={counts['ok']} skipped={counts['skipped']} failed={counts['failed']}", flush=True)


if __name__ == "__main__":
    main()
