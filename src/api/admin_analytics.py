"""Reepo API — admin analytics endpoint."""
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/api/admin/analytics")
def api_admin_analytics(days: int = Query(30, ge=1, le=365)):
    from src.server import get_db_path
    from src.analytics import get_analytics_summary

    return get_analytics_summary(get_db_path(), days=days)
