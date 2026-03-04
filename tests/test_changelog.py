"""Tests for changelog — record events, milestone detection, score changes."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.growth.db import init_growth_db
from src.growth.changelog import (
    record_event, get_repo_changelog,
    detect_milestones, detect_score_changes,
    MILESTONE_THRESHOLDS,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_growth_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def repo_db(db_path):
    repo_id = insert_repo({
        "github_id": 1, "owner": "org", "name": "repo",
        "full_name": "org/repo", "stars": 500,
        "language": "Python", "category_primary": "frameworks",
    }, db_path)
    return db_path, repo_id


class TestRecordEvent:
    def test_record_returns_id(self, repo_db):
        path, repo_id = repo_db
        eid = record_event(repo_id, "milestone", "Hit 500 stars", path=path)
        assert eid > 0

    def test_record_with_data(self, repo_db):
        path, repo_id = repo_db
        eid = record_event(
            repo_id, "score_change", "Score up",
            data={"old": 70, "new": 80}, path=path,
        )
        events = get_repo_changelog(repo_id, path=path)
        assert events[0]["data"]["old"] == 70

    def test_record_with_description(self, repo_db):
        path, repo_id = repo_db
        eid = record_event(
            repo_id, "milestone", "Title",
            description="Detailed description", path=path,
        )
        events = get_repo_changelog(repo_id, path=path)
        assert events[0]["description"] == "Detailed description"

    def test_record_multiple_events(self, repo_db):
        path, repo_id = repo_db
        record_event(repo_id, "milestone", "Event 1", path=path)
        record_event(repo_id, "milestone", "Event 2", path=path)
        record_event(repo_id, "score_change", "Event 3", path=path)
        events = get_repo_changelog(repo_id, path=path)
        assert len(events) == 3


class TestGetRepoChangelog:
    def test_empty_changelog(self, repo_db):
        path, repo_id = repo_db
        events = get_repo_changelog(repo_id, path=path)
        assert events == []

    def test_ordered_newest_first(self, repo_db):
        path, repo_id = repo_db
        record_event(repo_id, "milestone", "First", path=path)
        record_event(repo_id, "milestone", "Second", path=path)
        events = get_repo_changelog(repo_id, path=path)
        assert events[0]["title"] == "Second"
        assert events[1]["title"] == "First"

    def test_limit_respected(self, repo_db):
        path, repo_id = repo_db
        for i in range(10):
            record_event(repo_id, "milestone", f"Event {i}", path=path)
        events = get_repo_changelog(repo_id, limit=3, path=path)
        assert len(events) == 3

    def test_data_json_parsed(self, repo_db):
        path, repo_id = repo_db
        record_event(
            repo_id, "milestone", "Stars",
            data={"threshold": 1000}, path=path,
        )
        events = get_repo_changelog(repo_id, path=path)
        assert isinstance(events[0]["data"], dict)
        assert events[0]["data"]["threshold"] == 1000

    def test_different_repos_isolated(self, db_path):
        r1 = insert_repo({
            "github_id": 10, "owner": "a", "name": "a",
            "full_name": "a/a", "stars": 10, "language": "Python",
            "category_primary": "apps",
        }, db_path)
        r2 = insert_repo({
            "github_id": 20, "owner": "b", "name": "b",
            "full_name": "b/b", "stars": 20, "language": "Go",
            "category_primary": "apps",
        }, db_path)
        record_event(r1, "milestone", "Repo A event", path=db_path)
        record_event(r2, "milestone", "Repo B event", path=db_path)
        assert len(get_repo_changelog(r1, path=db_path)) == 1
        assert len(get_repo_changelog(r2, path=db_path)) == 1


class TestDetectMilestones:
    def test_single_milestone(self):
        milestones = detect_milestones(1, 150, 50)
        assert len(milestones) == 1
        assert milestones[0]["data"]["threshold"] == 100

    def test_multiple_milestones(self):
        milestones = detect_milestones(1, 1200, 50)
        thresholds = [m["data"]["threshold"] for m in milestones]
        assert 100 in thresholds
        assert 500 in thresholds
        assert 1000 in thresholds

    def test_exact_threshold(self):
        milestones = detect_milestones(1, 100, 99)
        assert len(milestones) == 1
        assert milestones[0]["data"]["threshold"] == 100

    def test_no_milestone_crossed(self):
        milestones = detect_milestones(1, 450, 400)
        assert milestones == []

    def test_all_thresholds(self):
        milestones = detect_milestones(1, 10000, 0)
        assert len(milestones) == len(MILESTONE_THRESHOLDS)

    def test_already_past_milestone(self):
        milestones = detect_milestones(1, 200, 150)
        assert milestones == []

    def test_exact_at_prev(self):
        """prev_stars == threshold should not trigger."""
        milestones = detect_milestones(1, 200, 100)
        assert milestones == []

    def test_milestone_data_structure(self):
        milestones = detect_milestones(1, 600, 400)
        assert len(milestones) == 1
        m = milestones[0]
        assert m["repo_id"] == 1
        assert m["event_type"] == "milestone"
        assert "Reached" in m["title"]
        assert m["data"]["threshold"] == 500
        assert m["data"]["current_stars"] == 600
        assert m["data"]["prev_stars"] == 400


class TestDetectScoreChanges:
    def test_significant_increase(self):
        changes = detect_score_changes(1, 85, 70)
        assert len(changes) == 1
        assert "increased" in changes[0]["title"]
        assert changes[0]["data"]["diff"] == 15

    def test_significant_decrease(self):
        changes = detect_score_changes(1, 60, 75)
        assert len(changes) == 1
        assert "decreased" in changes[0]["title"]
        assert changes[0]["data"]["diff"] == -15

    def test_below_threshold_no_change(self):
        changes = detect_score_changes(1, 72, 70)
        assert changes == []

    def test_exact_threshold(self):
        changes = detect_score_changes(1, 75, 70, threshold=5)
        assert len(changes) == 1

    def test_custom_threshold(self):
        changes = detect_score_changes(1, 80, 70, threshold=15)
        assert changes == []
        changes = detect_score_changes(1, 85, 70, threshold=15)
        assert len(changes) == 1

    def test_no_change(self):
        changes = detect_score_changes(1, 70, 70)
        assert changes == []

    def test_score_change_data_structure(self):
        changes = detect_score_changes(1, 90, 50)
        c = changes[0]
        assert c["repo_id"] == 1
        assert c["event_type"] == "score_change"
        assert c["data"]["new_score"] == 90
        assert c["data"]["old_score"] == 50
