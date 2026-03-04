"""Reepo API — sponsor routes."""
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/api/sponsors/listing")
def get_sponsored_listing(
    category: str | None = Query(None, description="Category to match"),
):
    from src.server import get_db_path
    from src.monetization.sponsors import get_active_sponsored_for_category, record_impression

    db_path = get_db_path()
    listing = get_active_sponsored_for_category(category=category, path=db_path)
    if not listing:
        return {"sponsored": None}

    record_impression(listing["id"], path=db_path)
    return {"sponsored": listing}


@router.post("/api/sponsors/click/{listing_id}")
def click_sponsored(listing_id: int):
    from src.server import get_db_path
    from src.monetization.sponsors import record_click

    db_path = get_db_path()
    record_click(listing_id, path=db_path)
    return {"status": "recorded"}


@router.get("/api/sponsors/dashboard")
def sponsor_dashboard(sponsor_id: int = Query(..., description="Sponsor ID")):
    from src.server import get_db_path
    from src.monetization.sponsors import get_sponsor_analytics

    db_path = get_db_path()
    return get_sponsor_analytics(sponsor_id, path=db_path)
