"""Reepo open data export — CC-BY-4.0 licensed CSV dump of the index."""
from __future__ import annotations

import csv
import io
import os
import tempfile
from datetime import datetime, timezone

from src.db import _connect, DEFAULT_DB_PATH


EXPORT_FIELDS = [
    "full_name", "description", "url", "stars", "forks", "language",
    "license", "category_primary", "reepo_score", "score_breakdown",
    "topics", "last_analyzed_at",
]

CC_BY_HEADER = (
    "# Reepo.dev Open Data Export\n"
    "# License: CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)\n"
    "# Attribution: Reepo.dev (https://reepo.dev)\n"
    "# Generated: {timestamp}\n"
    "# Total repos: {total}\n"
)


def generate_open_data_export(db_path: str = DEFAULT_DB_PATH, output_dir: str = "data") -> str:
    """Generate a CC-BY-4.0 CSV export of the full index. Returns file path."""
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT full_name, description, url, stars, forks, language, license, "
        "category_primary, reepo_score, score_breakdown, topics, last_analyzed_at "
        "FROM repos ORDER BY stars DESC"
    ).fetchall()
    conn.close()

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"reepo-open-data-{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        # Write license header as comments
        f.write(CC_BY_HEADER.format(timestamp=timestamp, total=len(rows)))
        writer = csv.writer(f)
        writer.writerow(EXPORT_FIELDS)
        for row in rows:
            writer.writerow([row[field] for field in EXPORT_FIELDS])

    return filepath


def generate_open_data_csv_string(db_path: str = DEFAULT_DB_PATH) -> str:
    """Generate CSV export as a string (for API endpoint)."""
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT full_name, description, url, stars, forks, language, license, "
        "category_primary, reepo_score, score_breakdown, topics, last_analyzed_at "
        "FROM repos ORDER BY stars DESC"
    ).fetchall()
    conn.close()

    output = io.StringIO()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output.write(CC_BY_HEADER.format(timestamp=timestamp, total=len(rows)))
    writer = csv.writer(output)
    writer.writerow(EXPORT_FIELDS)
    for row in rows:
        writer.writerow([row[field] for field in EXPORT_FIELDS])

    return output.getvalue()
