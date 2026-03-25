"""Re-classify all repos using full taxonomy (including design categories) and score unscored repos."""
import sqlite3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.taxonomy import classify_repo
from src.analyzer import analyze_repo
from src.db import CATEGORIES, DEFAULT_DB_PATH

DB_PATH = os.environ.get("REEPO_DB_PATH", DEFAULT_DB_PATH)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 1. Insert missing categories
    for slug, name, desc in CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO categories (slug, name, description) VALUES (?, ?, ?)",
            (slug, name, desc),
        )
    conn.commit()
    print(f"Categories ensured: {len(CATEGORIES)}")

    # 2. Reclassify all repos
    rows = conn.execute("SELECT id, full_name, description, topics, language, homepage FROM repos").fetchall()
    reclassified = 0
    design_count = 0

    for row in rows:
        repo_dict = {
            "full_name": row["full_name"],
            "description": row["description"] or "",
            "topics": json.loads(row["topics"]) if row["topics"] else [],
            "language": row["language"] or "",
            "homepage": row["homepage"] or "",
        }
        primary, secondary = classify_repo(
            row["full_name"],
            row["description"] or "",
            json.loads(row["topics"]) if row["topics"] else [],
        )

        old_primary = conn.execute("SELECT category_primary FROM repos WHERE id=?", (row["id"],)).fetchone()[0]
        if primary != old_primary:
            reclassified += 1
            if primary in ("ui-components", "design-systems", "css-styling", "icons-assets", "animation", "design-tools"):
                design_count += 1

        conn.execute(
            "UPDATE repos SET category_primary=?, categories_secondary=? WHERE id=?",
            (primary, json.dumps(secondary), row["id"]),
        )

    conn.commit()
    print(f"Reclassified: {reclassified} repos ({design_count} into design categories)")

    # 3. Update category counts
    for slug, name, desc in CATEGORIES:
        count = conn.execute("SELECT COUNT(*) FROM repos WHERE category_primary=?", (slug,)).fetchone()[0]
        conn.execute("UPDATE categories SET repo_count=? WHERE slug=?", (count, slug))
    conn.commit()

    # Print category breakdown
    print("\nCategory breakdown:")
    for row in conn.execute("SELECT slug, repo_count FROM categories ORDER BY repo_count DESC"):
        print(f"  {row[0]}: {row[1]}")

    # 4. Score unscored repos
    unscored = conn.execute(
        "SELECT id, full_name, description, stars, forks, language, license, topics, "
        "open_issues, has_wiki, homepage, created_at, updated_at, pushed_at "
        "FROM repos WHERE reepo_score IS NULL OR reepo_score = 0"
    ).fetchall()

    print(f"\nScoring {len(unscored)} unscored repos...")
    scored = 0
    for row in unscored:
        repo_dict = {
            "full_name": row["full_name"],
            "description": row["description"] or "",
            "stars": row["stars"] or 0,
            "forks": row["forks"] or 0,
            "language": row["language"] or "",
            "license": row["license"] or "",
            "topics": json.loads(row["topics"]) if row["topics"] else [],
            "open_issues": row["open_issues"] or 0,
            "has_wiki": row["has_wiki"] or 0,
            "homepage": row["homepage"] or "",
            "created_at": row["created_at"] or "",
            "updated_at": row["updated_at"] or "",
            "pushed_at": row["pushed_at"] or "",
        }
        try:
            result = analyze_repo(repo_dict)
            conn.execute(
                "UPDATE repos SET reepo_score=?, score_breakdown=?, last_analyzed_at=CURRENT_TIMESTAMP WHERE id=?",
                (result["reepo_score"], json.dumps(result["score_breakdown"]), row["id"]),
            )
            scored += 1
            if scored % 1000 == 0:
                conn.commit()
                print(f"  Scored {scored}/{len(unscored)}...")
        except Exception as e:
            print(f"  Error scoring {row['full_name']}: {e}")

    conn.commit()
    print(f"Scored: {scored} repos")

    # Score distribution
    print("\nScore distribution:")
    for row in conn.execute("""
        SELECT 
            CASE 
                WHEN reepo_score >= 80 THEN '80-100'
                WHEN reepo_score >= 60 THEN '60-79'
                WHEN reepo_score >= 40 THEN '40-59'
                WHEN reepo_score >= 20 THEN '20-39'
                ELSE '0-19'
            END as bucket,
            COUNT(*) as cnt
        FROM repos
        WHERE reepo_score > 0
        GROUP BY bucket
        ORDER BY bucket DESC
    """):
        print(f"  {row[0]}: {row[1]}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
