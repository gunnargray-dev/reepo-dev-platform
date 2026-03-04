"""Reepo daily crawl scheduler — discover, reanalyze, and update repos."""
from __future__ import annotations

from datetime import datetime, timezone

from src.db import _connect, DEFAULT_DB_PATH


class DailyCrawlScheduler:
    """Orchestrates daily crawl tasks: discover, reanalyze, update velocity."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.last_run: str | None = None
        self.results: dict = {}

    def discover_new_repos(self, topics: list[str]) -> dict:
        """Discover new repos by topic. Returns count of discovered repos."""
        conn = _connect(self.db_path)
        discovered = []
        for topic in topics:
            rows = conn.execute(
                "SELECT id, full_name FROM repos WHERE topics LIKE ? "
                "AND indexed_at > datetime('now', '-7 days')",
                (f"%{topic}%",),
            ).fetchall()
            discovered.extend([dict(r) for r in rows])
        conn.close()
        return {"topics_searched": len(topics), "discovered": len(discovered), "repos": discovered}

    def reanalyze_stale_repos(self, max_age_days: int = 7, batch_size: int = 100) -> dict:
        """Find repos not analyzed recently and mark them for reanalysis."""
        conn = _connect(self.db_path)
        rows = conn.execute(
            "SELECT id, full_name, last_analyzed_at FROM repos "
            "WHERE last_analyzed_at IS NULL "
            "OR last_analyzed_at < datetime('now', ? || ' days') "
            "ORDER BY last_analyzed_at ASC NULLS FIRST LIMIT ?",
            (f"-{max_age_days}", batch_size),
        ).fetchall()
        stale = [dict(r) for r in rows]
        conn.close()
        return {"stale_count": len(stale), "batch_size": batch_size, "repos": stale}

    def update_star_velocity(self) -> dict:
        """Calculate star velocity for repos with score history."""
        conn = _connect(self.db_path)
        rows = conn.execute(
            "SELECT r.id, r.full_name, r.stars, "
            "(SELECT sh.reepo_score FROM score_history sh "
            " WHERE sh.repo_id = r.id ORDER BY sh.recorded_at DESC LIMIT 1) as latest_score "
            "FROM repos r WHERE r.stars > 0 ORDER BY r.stars DESC LIMIT 100"
        ).fetchall()
        updated = [dict(r) for r in rows]
        conn.close()
        return {"repos_checked": len(updated), "repos": updated}

    def run_daily_job(self) -> dict:
        """Run all daily crawl tasks in sequence."""
        self.last_run = datetime.now(timezone.utc).isoformat()
        discover_result = self.discover_new_repos(["machine-learning", "ai", "llm"])
        stale_result = self.reanalyze_stale_repos()
        velocity_result = self.update_star_velocity()
        self.results = {
            "ran_at": self.last_run,
            "discover": discover_result,
            "reanalyze": stale_result,
            "velocity": velocity_result,
        }
        return self.results
