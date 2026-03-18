"""Batch summarize all repo READMEs using Ollama."""
import sqlite3
import base64
import time
import httpx
import sys
import os

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
from src.api.repos import summarize_readme

DB = os.path.join(PROJECT_ROOT, "data", "reepo.db")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    raise SystemExit("GITHUB_TOKEN env var is required")
GH_HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
}

# Load already-processed repo IDs (summaries > 150 chars are LLM-generated)
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
done_ids = set(
    r[0]
    for r in conn.execute(
        "SELECT id FROM repos WHERE length(readme_excerpt) > 150"
    ).fetchall()
)
rows = conn.execute(
    "SELECT id, owner, name, description FROM repos ORDER BY stars DESC"
).fetchall()
total_all = len(rows)
rows = [r for r in rows if r["id"] not in done_ids]
total = len(rows)
conn.close()

print(f"Resuming: {total_all - total} already done, {total} remaining", flush=True)

gh = httpx.Client(timeout=15.0, follow_redirects=True)
updated = 0
failed = 0
start = time.time()

for i, row in enumerate(rows):
    owner, name, desc = row["owner"], row["name"], row["description"]
    try:
        resp = gh.get(
            f"https://api.github.com/repos/{owner}/{name}/readme", headers=GH_HEADERS
        )
        if resp.status_code == 200:
            content = base64.b64decode(resp.json().get("content", "")).decode(
                "utf-8", errors="replace"
            )
            summary = summarize_readme(content, f"{owner}/{name}", desc)
            if summary:
                db = sqlite3.connect(DB)
                db.execute(
                    "UPDATE repos SET readme_excerpt = ? WHERE id = ?",
                    (summary, row["id"]),
                )
                db.commit()
                db.close()
                updated += 1
            elif desc:
                db = sqlite3.connect(DB)
                db.execute(
                    "UPDATE repos SET readme_excerpt = ? WHERE id = ?",
                    (desc, row["id"]),
                )
                db.commit()
                db.close()
                updated += 1
            else:
                failed += 1
        else:
            if desc:
                db = sqlite3.connect(DB)
                db.execute(
                    "UPDATE repos SET readme_excerpt = ? WHERE id = ?",
                    (desc, row["id"]),
                )
                db.commit()
                db.close()
                updated += 1
            else:
                failed += 1
    except Exception as e:
        print(f"  ERROR {owner}/{name}: {e}", flush=True)
        failed += 1

    done = i + 1
    if done % 50 == 0:
        elapsed = time.time() - start
        rate = done / elapsed
        eta = (total - done) / rate
        print(
            f"[{done}/{total}] updated={updated} failed={failed} "
            f"rate={rate:.2f}/s eta={eta / 3600:.1f}h",
            flush=True,
        )

    # Check GitHub rate limit every 500
    if done % 500 == 0:
        try:
            rl = gh.get("https://api.github.com/rate_limit", headers=GH_HEADERS)
            remaining = rl.json()["resources"]["core"]["remaining"]
            if remaining < 200:
                reset_time = rl.json()["resources"]["core"]["reset"]
                wait = max(0, reset_time - time.time()) + 5
                print(f"  Rate limit low ({remaining}), sleeping {wait:.0f}s...", flush=True)
                time.sleep(wait)
            else:
                print(f"  GitHub rate limit: {remaining} remaining", flush=True)
        except:
            pass

gh.close()
elapsed = time.time() - start
print(
    f"Done. {updated} updated, {failed} failed out of {total}. "
    f"Took {elapsed / 3600:.1f}h"
)
