"""Reepo sponsors — sponsored listings with impression and click tracking."""
from __future__ import annotations

from datetime import date

from src.db import _connect, DEFAULT_DB_PATH


def create_sponsor(
    name: str,
    logo_url: str = "",
    website_url: str = "",
    contact_email: str = "",
    path: str = DEFAULT_DB_PATH,
) -> int:
    """Create a new sponsor and return its ID."""
    conn = _connect(path)
    cur = conn.execute(
        "INSERT INTO sponsors (name, logo_url, website_url, contact_email) VALUES (?, ?, ?, ?)",
        (name, logo_url, website_url, contact_email),
    )
    sponsor_id = cur.lastrowid
    conn.commit()
    conn.close()
    return sponsor_id


def create_listing(
    sponsor_id: int,
    repo_id: int,
    landing_url: str,
    start_date: str,
    end_date: str,
    path: str = DEFAULT_DB_PATH,
) -> int:
    """Create a sponsored listing and return its ID."""
    conn = _connect(path)
    cur = conn.execute(
        "INSERT INTO sponsored_listings (sponsor_id, repo_id, landing_url, start_date, end_date) "
        "VALUES (?, ?, ?, ?, ?)",
        (sponsor_id, repo_id, landing_url, start_date, end_date),
    )
    listing_id = cur.lastrowid
    conn.commit()
    conn.close()
    return listing_id


def get_active_sponsored_for_category(
    category: str | None = None, path: str = DEFAULT_DB_PATH
) -> dict | None:
    """Get an active sponsored listing for a category or globally."""
    conn = _connect(path)
    today = date.today().isoformat()
    if category:
        row = conn.execute(
            "SELECT sl.*, r.full_name, r.description, r.stars, r.reepo_score, "
            "r.category_primary, r.language, s.name as sponsor_name, s.logo_url as sponsor_logo "
            "FROM sponsored_listings sl "
            "JOIN repos r ON sl.repo_id = r.id "
            "JOIN sponsors s ON sl.sponsor_id = s.id "
            "WHERE sl.is_active = 1 AND sl.start_date <= ? AND sl.end_date >= ? "
            "AND r.category_primary = ? "
            "ORDER BY sl.impressions ASC LIMIT 1",
            (today, today, category),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT sl.*, r.full_name, r.description, r.stars, r.reepo_score, "
            "r.category_primary, r.language, s.name as sponsor_name, s.logo_url as sponsor_logo "
            "FROM sponsored_listings sl "
            "JOIN repos r ON sl.repo_id = r.id "
            "JOIN sponsors s ON sl.sponsor_id = s.id "
            "WHERE sl.is_active = 1 AND sl.start_date <= ? AND sl.end_date >= ? "
            "ORDER BY sl.impressions ASC LIMIT 1",
            (today, today),
        ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def record_impression(listing_id: int, path: str = DEFAULT_DB_PATH) -> None:
    """Increment impression count for a listing."""
    conn = _connect(path)
    conn.execute(
        "UPDATE sponsored_listings SET impressions = impressions + 1 WHERE id = ?",
        (listing_id,),
    )
    conn.commit()
    conn.close()


def record_click(listing_id: int, path: str = DEFAULT_DB_PATH) -> None:
    """Increment click count for a listing."""
    conn = _connect(path)
    conn.execute(
        "UPDATE sponsored_listings SET clicks = clicks + 1 WHERE id = ?",
        (listing_id,),
    )
    conn.commit()
    conn.close()


def get_sponsor_analytics(
    sponsor_id: int, path: str = DEFAULT_DB_PATH
) -> dict:
    """Get analytics for a sponsor's listings."""
    conn = _connect(path)
    sponsor = conn.execute(
        "SELECT * FROM sponsors WHERE id = ?", (sponsor_id,)
    ).fetchone()
    if not sponsor:
        conn.close()
        return {"error": "Sponsor not found"}

    listings = conn.execute(
        "SELECT sl.*, r.full_name FROM sponsored_listings sl "
        "JOIN repos r ON sl.repo_id = r.id "
        "WHERE sl.sponsor_id = ? ORDER BY sl.created_at DESC",
        (sponsor_id,),
    ).fetchall()
    conn.close()

    total_impressions = sum(l["impressions"] for l in listings)
    total_clicks = sum(l["clicks"] for l in listings)
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0

    return {
        "sponsor": dict(sponsor),
        "listings": [dict(l) for l in listings],
        "totals": {
            "impressions": total_impressions,
            "clicks": total_clicks,
            "ctr": round(ctr, 2),
        },
    }
