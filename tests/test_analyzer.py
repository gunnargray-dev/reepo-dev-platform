"""Tests for the Reepo analyzer scoring pipeline."""
import math
from datetime import datetime, timedelta, timezone

import pytest

from src.analyzer import (
    analyze_repo,
    analyze_all_unscored,
    _score_maintenance,
    _score_documentation,
    _score_community,
    _score_popularity,
    _score_freshness,
    _score_license,
    WEIGHTS,
    PERMISSIVE_LICENSES,
    COPYLEFT_LICENSES,
)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _days_ago(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _make_repo(**overrides):
    base = {
        "id": 1,
        "github_id": 1001,
        "owner": "test",
        "name": "test-repo",
        "full_name": "test/test-repo",
        "description": "A test repository",
        "stars": 1000,
        "forks": 100,
        "language": "Python",
        "license": "MIT",
        "topics": ["ai"],
        "open_issues": 50,
        "has_wiki": True,
        "homepage": "https://test.dev",
        "readme_excerpt": "This is a comprehensive README with plenty of content for testing. " * 30,
        "created_at": _days_ago(365),
        "updated_at": _days_ago(5),
        "pushed_at": _days_ago(5),
    }
    base.update(overrides)
    return base


# --- WEIGHTS ---

class TestWeights:
    def test_weights_sum_to_one(self):
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_all_weights_positive(self):
        for key, weight in WEIGHTS.items():
            assert weight > 0, f"{key} has non-positive weight"

    def test_six_dimensions(self):
        assert len(WEIGHTS) == 6


# --- Maintenance Health ---

class TestMaintenanceHealth:
    def test_recent_push(self):
        repo = _make_repo(pushed_at=_days_ago(5))
        assert _score_maintenance(repo) == 100

    def test_push_29_days(self):
        repo = _make_repo(pushed_at=_days_ago(29))
        assert _score_maintenance(repo) == 100

    def test_push_31_days(self):
        repo = _make_repo(pushed_at=_days_ago(31))
        assert _score_maintenance(repo) == 70

    def test_push_60_days(self):
        repo = _make_repo(pushed_at=_days_ago(60))
        assert _score_maintenance(repo) == 70

    def test_push_91_days(self):
        repo = _make_repo(pushed_at=_days_ago(91))
        assert _score_maintenance(repo) == 40

    def test_push_120_days(self):
        repo = _make_repo(pushed_at=_days_ago(120))
        assert _score_maintenance(repo) == 40

    def test_push_181_days(self):
        repo = _make_repo(pushed_at=_days_ago(181))
        assert _score_maintenance(repo) == 20

    def test_push_250_days(self):
        repo = _make_repo(pushed_at=_days_ago(250))
        assert _score_maintenance(repo) == 20

    def test_push_366_days(self):
        repo = _make_repo(pushed_at=_days_ago(366))
        assert _score_maintenance(repo) == 0

    def test_push_500_days(self):
        repo = _make_repo(pushed_at=_days_ago(500))
        assert _score_maintenance(repo) == 0

    def test_no_push_date(self):
        repo = _make_repo(pushed_at=None)
        assert _score_maintenance(repo) == 0


# --- Documentation Quality ---

class TestDocumentationQuality:
    def test_long_readme(self):
        repo = _make_repo(readme_excerpt="x" * 3000)
        assert _score_documentation(repo) >= 100

    def test_medium_readme(self):
        repo = _make_repo(readme_excerpt="x" * 800)
        score = _score_documentation(repo)
        assert score >= 70

    def test_short_readme(self):
        repo = _make_repo(readme_excerpt="x" * 200, has_wiki=False, homepage=None)
        score = _score_documentation(repo)
        assert score == 40

    def test_minimal_readme(self):
        repo = _make_repo(readme_excerpt="x" * 50, has_wiki=False, homepage=None)
        score = _score_documentation(repo)
        assert score == 10

    def test_wiki_bonus(self):
        repo = _make_repo(readme_excerpt="x" * 800, has_wiki=True, homepage=None)
        score = _score_documentation(repo)
        assert score >= 80

    def test_homepage_bonus(self):
        repo = _make_repo(readme_excerpt="x" * 800, has_wiki=False, homepage="https://test.dev")
        score = _score_documentation(repo)
        assert score >= 80

    def test_both_bonuses(self):
        repo = _make_repo(readme_excerpt="x" * 800, has_wiki=True, homepage="https://test.dev")
        score = _score_documentation(repo)
        assert score >= 90

    def test_empty_readme(self):
        repo = _make_repo(readme_excerpt="", has_wiki=False, homepage=None)
        assert _score_documentation(repo) == 10

    def test_none_readme(self):
        repo = _make_repo(readme_excerpt=None, has_wiki=False, homepage=None)
        assert _score_documentation(repo) == 10

    def test_max_cap_at_100(self):
        repo = _make_repo(readme_excerpt="x" * 5000, has_wiki=True, homepage="https://test.dev")
        assert _score_documentation(repo) <= 100


# --- Community Activity ---

class TestCommunityActivity:
    def test_mega_popular(self):
        repo = _make_repo(stars=50000, forks=5000, open_issues=100)
        score = _score_community(repo)
        assert score >= 80

    def test_popular(self):
        repo = _make_repo(stars=5000, forks=500, open_issues=50)
        score = _score_community(repo)
        assert score >= 60

    def test_moderate(self):
        repo = _make_repo(stars=500, forks=50, open_issues=10)
        score = _score_community(repo)
        assert score >= 40

    def test_small(self):
        repo = _make_repo(stars=5, forks=1, open_issues=0)
        score = _score_community(repo)
        assert score <= 40

    def test_zero_stars(self):
        repo = _make_repo(stars=0, forks=0, open_issues=0)
        score = _score_community(repo)
        assert 0 <= score <= 100

    def test_high_issue_ratio(self):
        repo1 = _make_repo(stars=1000, forks=100, open_issues=500)
        repo2 = _make_repo(stars=1000, forks=100, open_issues=5)
        assert _score_community(repo2) >= _score_community(repo1)


# --- Popularity ---

class TestPopularity:
    def test_mega_stars(self):
        repo = _make_repo(stars=100000, forks=10000)
        score = _score_popularity(repo)
        assert score >= 80

    def test_popular(self):
        repo = _make_repo(stars=10000, forks=1000)
        score = _score_popularity(repo)
        assert score >= 60

    def test_moderate(self):
        repo = _make_repo(stars=100, forks=20)
        score = _score_popularity(repo)
        assert 20 <= score <= 60

    def test_zero_everything(self):
        repo = _make_repo(stars=0, forks=0)
        assert _score_popularity(repo) == 0

    def test_one_star(self):
        repo = _make_repo(stars=1, forks=0)
        score = _score_popularity(repo)
        assert 0 <= score <= 20

    def test_capped_at_100(self):
        repo = _make_repo(stars=1000000, forks=500000)
        assert _score_popularity(repo) <= 100


# --- Freshness ---

class TestFreshness:
    def test_very_fresh(self):
        repo = _make_repo(pushed_at=_days_ago(1), created_at=_days_ago(500))
        score = _score_freshness(repo)
        assert score >= 90

    def test_recent(self):
        repo = _make_repo(pushed_at=_days_ago(15), created_at=_days_ago(500))
        score = _score_freshness(repo)
        assert score >= 80

    def test_moderate(self):
        repo = _make_repo(pushed_at=_days_ago(60), created_at=_days_ago(500))
        score = _score_freshness(repo)
        assert score >= 60

    def test_stale(self):
        repo = _make_repo(pushed_at=_days_ago(200), created_at=_days_ago(500))
        score = _score_freshness(repo)
        assert score <= 50

    def test_abandoned(self):
        repo = _make_repo(pushed_at=_days_ago(500), created_at=_days_ago(1000))
        score = _score_freshness(repo)
        assert score <= 40

    def test_new_and_fresh(self):
        repo = _make_repo(pushed_at=_days_ago(1), created_at=_days_ago(30))
        score = _score_freshness(repo)
        assert score >= 80

    def test_no_push_date(self):
        repo = _make_repo(pushed_at=None, created_at=_days_ago(100))
        score = _score_freshness(repo)
        assert score <= 30

    def test_capped_at_100(self):
        repo = _make_repo(pushed_at=_days_ago(0), created_at=_days_ago(2000))
        assert _score_freshness(repo) <= 100


# --- License Score ---

class TestLicenseScore:
    def test_mit(self):
        assert _score_license({"license": "MIT"}) == 100

    def test_apache(self):
        assert _score_license({"license": "Apache-2.0"}) == 100

    def test_bsd_3(self):
        assert _score_license({"license": "BSD-3-Clause"}) == 100

    def test_bsd_2(self):
        assert _score_license({"license": "BSD-2-Clause"}) == 100

    def test_isc(self):
        assert _score_license({"license": "ISC"}) == 100

    def test_unlicense(self):
        assert _score_license({"license": "Unlicense"}) == 100

    def test_gpl_3(self):
        assert _score_license({"license": "GPL-3.0"}) == 70

    def test_agpl_3(self):
        assert _score_license({"license": "AGPL-3.0"}) == 70

    def test_lgpl(self):
        assert _score_license({"license": "LGPL-2.1"}) == 70

    def test_mpl(self):
        assert _score_license({"license": "MPL-2.0"}) == 70

    def test_unknown_license(self):
        assert _score_license({"license": "Artistic-2.0"}) == 50

    def test_no_license(self):
        assert _score_license({"license": None}) == 30

    def test_empty_license(self):
        assert _score_license({"license": ""}) == 30

    def test_noassertion(self):
        assert _score_license({"license": "NOASSERTION"}) == 30

    def test_all_permissive(self):
        for lic in PERMISSIVE_LICENSES:
            assert _score_license({"license": lic}) == 100

    def test_all_copyleft(self):
        for lic in COPYLEFT_LICENSES:
            assert _score_license({"license": lic}) == 70


# --- analyze_repo ---

class TestAnalyzeRepo:
    def test_returns_dict(self):
        result = analyze_repo(_make_repo())
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = analyze_repo(_make_repo())
        assert "reepo_score" in result
        assert "score_breakdown" in result
        assert "analyzed_at" in result

    def test_score_in_range(self):
        result = analyze_repo(_make_repo())
        assert 0 <= result["reepo_score"] <= 100

    def test_breakdown_has_all_dimensions(self):
        result = analyze_repo(_make_repo())
        for dim in WEIGHTS:
            assert dim in result["score_breakdown"]

    def test_breakdown_scores_in_range(self):
        result = analyze_repo(_make_repo())
        for dim, score in result["score_breakdown"].items():
            assert 0 <= score <= 100, f"{dim} out of range: {score}"

    def test_analyzed_at_is_iso(self):
        result = analyze_repo(_make_repo())
        datetime.fromisoformat(result["analyzed_at"])

    def test_healthy_active_repo_scores_high(self):
        repo = _make_repo(
            stars=10000,
            forks=1000,
            license="MIT",
            pushed_at=_days_ago(3),
            created_at=_days_ago(730),
            readme_excerpt="x" * 3000,
            has_wiki=True,
            homepage="https://test.dev",
            open_issues=50,
        )
        result = analyze_repo(repo)
        assert result["reepo_score"] >= 80

    def test_abandoned_repo_scores_low(self):
        repo = _make_repo(
            stars=3,
            forks=0,
            license=None,
            pushed_at=_days_ago(700),
            created_at=_days_ago(1000),
            readme_excerpt="minimal",
            has_wiki=False,
            homepage=None,
            open_issues=0,
        )
        result = analyze_repo(repo)
        assert result["reepo_score"] < 30

    def test_moderate_repo_scores_moderate(self):
        repo = _make_repo(
            stars=200,
            forks=20,
            license="Apache-2.0",
            pushed_at=_days_ago(45),
            created_at=_days_ago(400),
            readme_excerpt="x" * 600,
            has_wiki=False,
            homepage=None,
            open_issues=15,
        )
        result = analyze_repo(repo)
        assert 40 <= result["reepo_score"] <= 80

    def test_score_is_integer(self):
        result = analyze_repo(_make_repo())
        assert isinstance(result["reepo_score"], int)


# --- analyze_all_unscored ---

class TestAnalyzeAllUnscored:
    def test_with_db(self):
        import os
        import tempfile
        from src.db import init_db, insert_repo

        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        init_db(path)

        for i in range(3):
            insert_repo({
                "github_id": 20000 + i,
                "owner": "test",
                "name": f"repo-{i}",
                "full_name": f"test/repo-{i}",
                "stars": 100 * (i + 1),
                "forks": 10 * (i + 1),
                "language": "Python",
                "license": "MIT",
                "topics": ["ai"],
                "pushed_at": _days_ago(10),
                "created_at": _days_ago(200),
            }, path)

        count = analyze_all_unscored(path)
        assert count == 3

        from src.db import get_repo_by_id
        repo = get_repo_by_id(1, path)
        assert repo["reepo_score"] is not None
        assert repo["reepo_score"] > 0

        os.unlink(path)

    def test_skips_already_scored(self):
        import os
        import tempfile
        from src.db import init_db, insert_repo, record_score

        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        init_db(path)

        repo_id = insert_repo({
            "github_id": 21000,
            "owner": "test",
            "name": "scored-repo",
            "full_name": "test/scored-repo",
            "stars": 500,
            "forks": 50,
            "language": "Python",
            "license": "MIT",
            "topics": ["ai"],
            "pushed_at": _days_ago(5),
            "created_at": _days_ago(200),
        }, path)
        record_score(repo_id, 80, {"test": 80}, path)

        count = analyze_all_unscored(path)
        assert count == 0

        os.unlink(path)
