"""Refine repo summaries using Claude Haiku to sound natural, not LLM-generated."""
import sqlite3
import time
import os
import anthropic

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "reepo.db")
client = anthropic.Anthropic()

SYSTEM = """Rewrite the description to sound human-written. 2-3 sentences max. Be casual but accurate.

BANNED WORDS (never use these): comprehensive, powerful, robust, leveraging, utilizing, facilitates, empowers, cutting-edge, seamless, ecosystem, landscape, go-to, ensures, designed to, aims to, addresses the challenge, offers a, provides a framework, ultimately, essentially, garnered, cementing, expansive, extensive, diverse, streamline

BANNED OPENINGS (never start with): This project, This tool, This library, The project, The tool, The library, A comprehensive, A powerful

Just say what the thing does. Be specific. Plain text only, no markdown."""


def refine(summary: str, repo_name: str) -> str:
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"Rewrite this about paragraph for {repo_name}:\n\n{summary}"}],
    )
    return msg.content[0].text.strip()


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Track which ones we've already refined with a marker column
    try:
        conn.execute("ALTER TABLE repos ADD COLUMN haiku_refined INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass  # column already exists

    rows = conn.execute(
        "SELECT id, owner, name, readme_excerpt FROM repos "
        "WHERE length(readme_excerpt) > 50 AND haiku_refined = 0 "
        "ORDER BY stars DESC"
    ).fetchall()

    total = len(rows)
    print(f"Refining {total} summaries with Haiku...", flush=True)

    updated = 0
    failed = 0
    start = time.time()

    for i, row in enumerate(rows):
        repo_name = f"{row['owner']}/{row['name']}"
        try:
            refined = refine(row["readme_excerpt"], repo_name)
            if refined and len(refined) > 30:
                conn.execute(
                    "UPDATE repos SET readme_excerpt = ?, haiku_refined = 1 WHERE id = ?",
                    (refined, row["id"]),
                )
                conn.commit()
                updated += 1
            else:
                conn.execute("UPDATE repos SET haiku_refined = 1 WHERE id = ?", (row["id"],))
                conn.commit()
                failed += 1
        except anthropic.RateLimitError:
            print(f"  Rate limited at {i}, sleeping 30s...", flush=True)
            time.sleep(30)
            # retry
            try:
                refined = refine(row["readme_excerpt"], repo_name)
                if refined and len(refined) > 30:
                    conn.execute(
                        "UPDATE repos SET readme_excerpt = ?, haiku_refined = 1 WHERE id = ?",
                        (refined, row["id"]),
                    )
                    conn.commit()
                    updated += 1
            except:
                failed += 1
        except Exception as e:
            print(f"  ERROR {repo_name}: {e}", flush=True)
            failed += 1

        done = i + 1
        if done % 100 == 0:
            elapsed = time.time() - start
            rate = done / elapsed
            eta = (total - done) / rate
            print(
                f"[{done}/{total}] updated={updated} failed={failed} "
                f"rate={rate:.1f}/s eta={eta / 60:.0f}min",
                flush=True,
            )

    conn.close()
    elapsed = time.time() - start
    print(f"Done. {updated} refined, {failed} failed out of {total}. Took {elapsed / 60:.0f}min")


if __name__ == "__main__":
    main()
