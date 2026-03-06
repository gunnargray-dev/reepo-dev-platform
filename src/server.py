"""Reepo FastAPI server — app factory with CORS and middleware."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db import init_db, DEFAULT_DB_PATH
from src.search import init_fts
from src.trending import init_trending_tables
from src.middleware import RateLimiter
from src.monetization.db import init_monetization_db
from src.analytics import init_analytics_db
from src.community.contributors import init_contributor_db
from src.community.db import init_community_db
from src.growth.db import init_growth_db
from src.auth.db import init_auth_db
from src.collections.db import init_collections_db

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
    from src.api.sponsors import router as sponsors_router
    from src.api.billing import router as billing_router
    from src.api.comparison import router as comparison_router
    from src.api.export import router as export_router
    from src.api.newsletter import router as newsletter_router
    from src.api.public_stats import router as public_stats_router
    from src.api.admin_analytics import router as admin_analytics_router
    from src.api.open_data import router as open_data_router
    from src.api.contributors import router as contributors_router
    from src.api.community import router as community_router
    from src.api.admin import router as admin_router
    from src.api.blog import router as blog_router
    from src.api.badges import router as badges_router
    from src.api.scheduler import router as scheduler_router
    from src.api.recommendations import router as recommendations_router
    from src.api.changelog import router as changelog_router
    from src.api.seo import router as seo_router
    from src.api.auth import router as auth_router
    from src.api.collections import router as collections_router
    from src.api.bookmarks import router as bookmarks_router
    from src.api.users import router as users_router
    from src.api.api_keys import router as api_keys_router
    from src.api.slack import router as slack_router
    from src.api.discord import router as discord_router

    application.include_router(search_router)
    application.include_router(repos_router)
    application.include_router(categories_router)
    application.include_router(trending_router)
    application.include_router(stats_router)
    application.include_router(sponsors_router)
    application.include_router(billing_router)
    application.include_router(comparison_router)
    application.include_router(export_router)
    application.include_router(newsletter_router)
    application.include_router(public_stats_router)
    application.include_router(admin_analytics_router)
    application.include_router(open_data_router)
    application.include_router(contributors_router)
    application.include_router(community_router)
    application.include_router(admin_router)
    application.include_router(blog_router)
    application.include_router(badges_router)
    application.include_router(scheduler_router)
    application.include_router(recommendations_router)
    application.include_router(changelog_router)
    application.include_router(seo_router)
    application.include_router(auth_router)
    application.include_router(collections_router)
    application.include_router(bookmarks_router)
    application.include_router(users_router)
    application.include_router(api_keys_router)
    application.include_router(slack_router)
    application.include_router(discord_router)

    @application.on_event("startup")
    def startup():
        init_db(_db_path)
        init_fts(_db_path)
        init_trending_tables(_db_path)
        init_monetization_db(_db_path)
        init_analytics_db(_db_path)
        init_contributor_db(_db_path)
        init_community_db(_db_path)
        init_growth_db(_db_path)
        init_auth_db(_db_path)
        init_collections_db(_db_path)

    @application.get("/api/health")
    def health():
        return {"status": "ok"}

    return application


app = create_app()
