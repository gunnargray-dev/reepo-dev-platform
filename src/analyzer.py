"""Reepo analyzer — score repos on six dimensions to produce a Reepo Score."""
import math
from datetime import datetime, timezone

from src.db import (
    DEFAULT_DB_PATH,
    get_unscored_repos,
    record_score,
    get_repo_by_id,
    list_repos,
)

WEIGHTS = {
    "maintenance_health": 0.25,
    "documentation_quality": 0.15,
    "community_activity": 0.25,
    "popularity": 0.15,
    "freshness": 0.10,
    "license_score": 0.10,
}

# For repos < 90 days old, community+popularity weight is reduced and
# redistributed to maintenance, docs, and freshness. This prevents new
# repos from being penalized for not yet having stars/forks.
_YOUNG_WEIGHTS = {
    "maintenance_health": 0.30,
    "documentation_quality": 0.25,
    "community_activity": 0.10,
    "popularity": 0.10,
    "freshness": 0.15,
    "license_score": 0.10,
}

AGE_RAMP_DAYS = 90  # linear blend from _YOUNG_WEIGHTS to WEIGHTS over this period

PERMISSIVE_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense", "0BSD"}
COPYLEFT_LICENSES = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0", "MPL-2.0",
                     "GPL-2.0-only", "GPL-3.0-only", "AGPL-3.0-only"}


def _days_since(iso_date: str | None) -> float:
    if not iso_date:
        return 999
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return max(delta.total_seconds() / 86400, 0)
    except (ValueError, TypeError):
        return 999


def _score_maintenance(repo: dict) -> int:
    days = _days_since(repo.get("pushed_at"))
    if days <= 30:
        score = 100
    elif days <= 90:
        score = 70
    elif days <= 180:
        score = 40
    elif days <= 365:
        score = 20
    else:
        score = 0
    return score


def _score_documentation(repo: dict) -> int:
    readme = repo.get("readme_excerpt") or ""
    length = len(readme)

    if length > 2000:
        score = 100
    elif length > 500:
        score = 70
    elif length > 100:
        score = 40
    else:
        score = 10

    if repo.get("has_wiki"):
        score = min(100, score + 10)
    if repo.get("homepage"):
        score = min(100, score + 10)

    return score


def _score_community(repo: dict) -> int:
    stars = repo.get("stars", 0)
    forks = repo.get("forks", 0)

    if stars >= 10000:
        star_score = 100
    elif stars >= 1000:
        star_score = 80
    elif stars >= 100:
        star_score = 60
    elif stars >= 10:
        star_score = 40
    else:
        star_score = 20

    if forks >= 1000:
        fork_score = 100
    elif forks >= 100:
        fork_score = 70
    elif forks >= 10:
        fork_score = 40
    else:
        fork_score = 20

    open_issues = repo.get("open_issues", 0)
    if stars > 0:
        issue_ratio = open_issues / stars
        if issue_ratio < 0.01:
            issue_score = 90
        elif issue_ratio < 0.05:
            issue_score = 70
        elif issue_ratio < 0.1:
            issue_score = 50
        else:
            issue_score = 30
    else:
        issue_score = 50

    return round(star_score * 0.5 + fork_score * 0.3 + issue_score * 0.2)


def _score_popularity(repo: dict) -> int:
    stars = repo.get("stars", 0)
    forks = repo.get("forks", 0)

    if stars <= 0:
        star_score = 0
    else:
        star_score = min(100, round(math.log10(stars) / math.log10(100000) * 100))

    if forks <= 0:
        fork_score = 0
    else:
        fork_score = min(100, round(math.log10(forks) / math.log10(50000) * 100))

    return round(star_score * 0.7 + fork_score * 0.3)


def _score_freshness(repo: dict) -> int:
    push_days = _days_since(repo.get("pushed_at"))
    create_days = _days_since(repo.get("created_at"))

    if push_days <= 7:
        recency = 100
    elif push_days <= 30:
        recency = 85
    elif push_days <= 90:
        recency = 60
    elif push_days <= 180:
        recency = 35
    elif push_days <= 365:
        recency = 15
    else:
        recency = 0

    if create_days >= 365:
        maturity = 30
    elif create_days >= 90:
        maturity = 20
    else:
        maturity = 10

    return min(100, recency + maturity)


def _score_license(repo: dict) -> int:
    lic = repo.get("license") or ""
    if lic in PERMISSIVE_LICENSES:
        return 100
    if lic in COPYLEFT_LICENSES:
        return 70
    if lic and lic != "NOASSERTION":
        return 50
    return 30


def analyze_repo(repo: dict) -> dict:
    """Analyze a single repo and return scores.

    Returns dict with keys: reepo_score, score_breakdown, analyzed_at
    """
    breakdown = {
        "maintenance_health": _score_maintenance(repo),
        "documentation_quality": _score_documentation(repo),
        "community_activity": _score_community(repo),
        "popularity": _score_popularity(repo),
        "freshness": _score_freshness(repo),
        "license_score": _score_license(repo),
    }

    # Age-adjusted weights: linearly blend from young to standard over 90 days
    age_days = _days_since(repo.get("created_at"))
    t = min(age_days / AGE_RAMP_DAYS, 1.0)  # 0 = brand new, 1 = mature
    weights = {
        dim: _YOUNG_WEIGHTS[dim] + t * (WEIGHTS[dim] - _YOUNG_WEIGHTS[dim])
        for dim in WEIGHTS
    }

    weighted_sum = sum(breakdown[dim] * weights[dim] for dim in weights)
    reepo_score = round(weighted_sum)

    return {
        "reepo_score": reepo_score,
        "score_breakdown": breakdown,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def analyze_all_unscored(db_path: str = DEFAULT_DB_PATH) -> int:
    """Analyze all repos without a score. Returns count analyzed."""
    repos = get_unscored_repos(db_path)
    count = 0

    for repo in repos:
        result = analyze_repo(repo)
        record_score(
            repo["id"],
            result["reepo_score"],
            result["score_breakdown"],
            db_path,
        )
        count += 1

    return count
