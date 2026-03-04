"""Reepo API — admin crawl scheduler endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/api/admin/crawl/run")
def api_run_crawl():
    from src.server import get_db_path
    from src.growth.scheduler import DailyCrawlScheduler

    scheduler = DailyCrawlScheduler(db_path=get_db_path())
    results = scheduler.run_daily_job()
    return results


@router.get("/api/admin/crawl/status")
def api_crawl_status():
    from src.server import get_db_path
    from src.growth.scheduler import DailyCrawlScheduler

    scheduler = DailyCrawlScheduler(db_path=get_db_path())
    return {
        "last_run": scheduler.last_run,
        "results": scheduler.results,
    }
