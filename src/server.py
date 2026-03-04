"""Reepo FastAPI server — app factory with CORS and middleware."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db import init_db, DEFAULT_DB_PATH
from src.search import init_fts
from src.trending import init_trending_tables
from src.middleware import RateLimiter

_db_path: str = DEFAULT_DB_PATH


def get_db_path() -> str:
    """Return the configured database path."""
    return _db_path


def create_app(db_path: str | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    global _db_path
    _db_path = db_path or os.environ.get("REEPO_DB_PATH", DEFAULT_DB_PATH)

    application = FastAPI(
        title="Reepo.dev API",
        description="Open source discovery engine for AI repos",
        version="0.2.0",
    )

    application.state.db_path = _db_path

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RateLimiter, max_requests=100, window_seconds=60)

    from src.api.search_routes import router as search_router
    from src.api.repos import router as repos_router
    from src.api.categories import router as categories_router
    from src.api.trending import router as trending_router
    from src.api.stats import router as stats_router

    application.include_router(search_router)
    application.include_router(repos_router)
    application.include_router(categories_router)
    application.include_router(trending_router)
    application.include_router(stats_router)

    @application.on_event("startup")
    def startup():
        init_db(_db_path)
        init_fts(_db_path)
        init_trending_tables(_db_path)

    @application.get("/api/health")
    def health():
        return {"status": "ok"}

    return application


app = create_app()
