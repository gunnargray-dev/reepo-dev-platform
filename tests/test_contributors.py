"""Tests for the Reepo contributor program — roles, badges, permissions."""
import os
import tempfile

import pytest

from src.db import init_db
from src.community.contributors import (
    init_contributor_db,
    grant_role,
    revoke_role,
    get_user_roles,
    get_user_badges,
    has_permission,
    is_moderator,
    get_contributors_by_role,
    VALID_ROLES,
    ROLE_PERMISSIONS,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_contributor_db(path)
    yield path
    os.unlink(path)


class TestGrantRole:
    def test_grant_valid_role(self, db_path):
        assert grant_role(1, "moderator", path=db_path) is True

    def test_grant_all_valid_roles(self, db_path):
        for i, role in enumerate(VALID_ROLES):
            assert grant_role(100 + i, role, path=db_path) is True

    def test_grant_with_granted_by(self, db_path):
        assert grant_role(2, "contributor", granted_by=1, path=db_path) is True

    def test_grant_duplicate_returns_false(self, db_path):
        grant_role(3, "moderator", path=db_path)
        assert grant_role(3, "moderator", path=db_path) is False

    def test_grant_different_roles_same_user(self, db_path):
        assert grant_role(4, "moderator", path=db_path) is True
        assert grant_role(4, "contributor", path=db_path) is True

    def test_grant_invalid_role_raises(self, db_path):
        with pytest.raises(ValueError):
            grant_role(5, "admin", path=db_path)

    def test_grant_empty_role_raises(self, db_path):
        with pytest.raises(ValueError):
            grant_role(6, "", path=db_path)


class TestRevokeRole:
    def test_revoke_existing_role(self, db_path):
        grant_role(10, "moderator", path=db_path)
        assert revoke_role(10, "moderator", path=db_path) is True

    def test_revoke_nonexistent_role(self, db_path):
        assert revoke_role(11, "moderator", path=db_path) is False

    def test_revoke_removes_from_roles(self, db_path):
        grant_role(12, "moderator", path=db_path)
        revoke_role(12, "moderator", path=db_path)
        assert "moderator" not in get_user_roles(12, path=db_path)

    def test_double_revoke(self, db_path):
        grant_role(13, "contributor", path=db_path)
        assert revoke_role(13, "contributor", path=db_path) is True
        assert revoke_role(13, "contributor", path=db_path) is False


class TestGetUserRoles:
    def test_no_roles(self, db_path):
        assert get_user_roles(20, path=db_path) == []

    def test_single_role(self, db_path):
        grant_role(21, "moderator", path=db_path)
        roles = get_user_roles(21, path=db_path)
        assert roles == ["moderator"]

    def test_multiple_roles(self, db_path):
        grant_role(22, "moderator", path=db_path)
        grant_role(22, "contributor", path=db_path)
        roles = get_user_roles(22, path=db_path)
        assert len(roles) == 2
        assert "moderator" in roles
        assert "contributor" in roles


class TestGetUserBadges:
    def test_no_badges(self, db_path):
        assert get_user_badges(30, path=db_path) == []

    def test_badge_structure(self, db_path):
        grant_role(31, "moderator", path=db_path)
        badges = get_user_badges(31, path=db_path)
        assert len(badges) == 1
        badge = badges[0]
        assert "role" in badge
        assert "label" in badge
        assert "color" in badge
        assert "icon" in badge
        assert "granted_at" in badge

    def test_moderator_badge_values(self, db_path):
        grant_role(32, "moderator", path=db_path)
        badge = get_user_badges(32, path=db_path)[0]
        assert badge["label"] == "Moderator"
        assert badge["color"] == "blue"
        assert badge["icon"] == "shield"

    def test_contributor_badge_values(self, db_path):
        grant_role(33, "contributor", path=db_path)
        badge = get_user_badges(33, path=db_path)[0]
        assert badge["label"] == "Contributor"
        assert badge["color"] == "green"
        assert badge["icon"] == "heart"

    def test_verified_author_badge_values(self, db_path):
        grant_role(34, "verified_author", path=db_path)
        badge = get_user_badges(34, path=db_path)[0]
        assert badge["label"] == "Verified Author"
        assert badge["color"] == "purple"
        assert badge["icon"] == "check"

    def test_multiple_badges(self, db_path):
        grant_role(35, "moderator", path=db_path)
        grant_role(35, "verified_author", path=db_path)
        badges = get_user_badges(35, path=db_path)
        assert len(badges) == 2


class TestHasPermission:
    def test_moderator_has_approve_repos(self, db_path):
        grant_role(40, "moderator", path=db_path)
        assert has_permission(40, "approve_repos", path=db_path) is True

    def test_moderator_has_moderate_comments(self, db_path):
        grant_role(41, "moderator", path=db_path)
        assert has_permission(41, "moderate_comments", path=db_path) is True

    def test_moderator_has_view_reports(self, db_path):
        grant_role(42, "moderator", path=db_path)
        assert has_permission(42, "view_reports", path=db_path) is True

    def test_contributor_has_pro_access(self, db_path):
        grant_role(43, "contributor", path=db_path)
        assert has_permission(43, "pro_access", path=db_path) is True

    def test_contributor_has_badge_display(self, db_path):
        grant_role(44, "contributor", path=db_path)
        assert has_permission(44, "badge_display", path=db_path) is True

    def test_verified_author_has_author_highlight(self, db_path):
        grant_role(45, "verified_author", path=db_path)
        assert has_permission(45, "author_highlight", path=db_path) is True

    def test_no_role_no_permission(self, db_path):
        assert has_permission(46, "approve_repos", path=db_path) is False

    def test_wrong_role_no_permission(self, db_path):
        grant_role(47, "contributor", path=db_path)
        assert has_permission(47, "approve_repos", path=db_path) is False

    def test_multi_role_combined_permissions(self, db_path):
        grant_role(48, "moderator", path=db_path)
        grant_role(48, "contributor", path=db_path)
        assert has_permission(48, "approve_repos", path=db_path) is True
        assert has_permission(48, "pro_access", path=db_path) is True


class TestIsModerator:
    def test_is_moderator_true(self, db_path):
        grant_role(50, "moderator", path=db_path)
        assert is_moderator(50, path=db_path) is True

    def test_is_moderator_false(self, db_path):
        assert is_moderator(51, path=db_path) is False

    def test_contributor_is_not_moderator(self, db_path):
        grant_role(52, "contributor", path=db_path)
        assert is_moderator(52, path=db_path) is False


class TestGetContributorsByRole:
    def test_get_moderators(self, db_path):
        grant_role(60, "moderator", path=db_path)
        grant_role(61, "moderator", path=db_path)
        result = get_contributors_by_role("moderator", path=db_path)
        assert len(result) == 2

    def test_get_empty_role(self, db_path):
        result = get_contributors_by_role("moderator", path=db_path)
        assert result == []

    def test_invalid_role_returns_empty(self, db_path):
        result = get_contributors_by_role("invalid", path=db_path)
        assert result == []

    def test_contributor_entry_structure(self, db_path):
        grant_role(62, "contributor", granted_by=1, path=db_path)
        result = get_contributors_by_role("contributor", path=db_path)
        assert len(result) == 1
        entry = result[0]
        assert entry["user_id"] == 62
        assert entry["role"] == "contributor"
        assert entry["granted_by"] == 1
        assert "granted_at" in entry


class TestValidRolesConfig:
    def test_valid_roles_count(self):
        assert len(VALID_ROLES) == 3

    def test_all_roles_have_permissions(self):
        for role in VALID_ROLES:
            assert role in ROLE_PERMISSIONS
            assert len(ROLE_PERMISSIONS[role]) > 0
