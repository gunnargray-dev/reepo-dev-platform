"""Reepo API — open data download endpoint."""
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()


@router.get("/api/open-data/latest.csv")
def api_open_data_csv():
    from src.server import get_db_path
    from src.open_data import generate_open_data_csv_string

    csv_content = generate_open_data_csv_string(get_db_path())
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reepo-open-data.csv"},
    )
