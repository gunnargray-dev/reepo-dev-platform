"""Tests for comments module — add, thread, edit, delete, flag, get threaded."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.community.db import init_community_db
from src.community.comments import (
    add_comment, get_comments, update_comment,
    delete_comment, flag_comment, get_flagged_comments,
    sanitize_comment_body, MAX_COMMENT_LENGTH,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_community_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def repo_db(db_path):
    repo_id = insert_repo({
        "github_id": 1, "owner": "org1", "name": "repo1",
        "full_name": "org1/repo1", "stars": 100, "language": "Python",
        "category_primary": "frameworks",
    }, db_path)
    return db_path, repo_id


class TestAddComment:
    def test_add_returns_id(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "Great repo!", path=path)
        assert cid > 0

    def test_add_with_parent(self, repo_db):
        path, repo_id = repo_db
        parent_id = add_comment(1, repo_id, "First comment", path=path)
        reply_id = add_comment(2, repo_id, "Reply!", parent_id=parent_id, path=path)
        assert reply_id > parent_id

    def test_add_multiple_comments(self, repo_db):
        path, repo_id = repo_db
        cid1 = add_comment(1, repo_id, "Comment 1", path=path)
        cid2 = add_comment(2, repo_id, "Comment 2", path=path)
        assert cid1 != cid2


class TestGetComments:
    def test_get_threaded(self, repo_db):
        path, repo_id = repo_db
        parent_id = add_comment(1, repo_id, "Top-level", path=path)
        add_comment(2, repo_id, "Reply 1", parent_id=parent_id, path=path)
        add_comment(3, repo_id, "Reply 2", parent_id=parent_id, path=path)

        comments = get_comments(repo_id, path=path)
        assert len(comments) == 1  # Only top-level
        assert len(comments[0]["replies"]) == 2

    def test_get_multiple_top_level(self, repo_db):
        path, repo_id = repo_db
        add_comment(1, repo_id, "First", path=path)
        add_comment(2, repo_id, "Second", path=path)
        comments = get_comments(repo_id, path=path)
        assert len(comments) == 2

    def test_get_empty(self, repo_db):
        path, repo_id = repo_db
        comments = get_comments(repo_id, path=path)
        assert comments == []

    def test_get_with_limit(self, repo_db):
        path, repo_id = repo_db
        for i in range(10):
            add_comment(i, repo_id, f"Comment {i}", path=path)
        comments = get_comments(repo_id, limit=5, path=path)
        assert len(comments) == 5

    def test_nested_replies_in_parent(self, repo_db):
        path, repo_id = repo_db
        top = add_comment(1, repo_id, "Top", path=path)
        r1 = add_comment(2, repo_id, "R1", parent_id=top, path=path)

        comments = get_comments(repo_id, path=path)
        assert comments[0]["body"] == "Top"
        assert comments[0]["replies"][0]["body"] == "R1"


class TestUpdateComment:
    def test_update_own_comment(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "Original", path=path)
        assert update_comment(cid, 1, "Updated", path=path) is True

    def test_update_other_user_fails(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "Original", path=path)
        assert update_comment(cid, 2, "Hacked", path=path) is False

    def test_update_nonexistent(self, repo_db):
        path, _ = repo_db
        assert update_comment(999, 1, "No", path=path) is False


class TestDeleteComment:
    def test_delete_own_comment(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "Delete me", path=path)
        assert delete_comment(cid, 1, path=path) is True
        comments = get_comments(repo_id, path=path)
        assert len(comments) == 0

    def test_delete_other_user_fails(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "Protected", path=path)
        assert delete_comment(cid, 2, path=path) is False

    def test_delete_nonexistent(self, repo_db):
        path, _ = repo_db
        assert delete_comment(999, 1, path=path) is False


class TestFlagComment:
    def test_flag_comment(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "Bad comment", path=path)
        assert flag_comment(cid, path=path) is True

    def test_flag_nonexistent(self, repo_db):
        path, _ = repo_db
        assert flag_comment(999, path=path) is False

    def test_get_flagged(self, repo_db):
        path, repo_id = repo_db
        cid1 = add_comment(1, repo_id, "Bad 1", path=path)
        cid2 = add_comment(2, repo_id, "Good", path=path)
        cid3 = add_comment(3, repo_id, "Bad 2", path=path)
        flag_comment(cid1, path=path)
        flag_comment(cid3, path=path)
        flagged = get_flagged_comments(path=path)
        assert len(flagged) == 2
        flagged_ids = [c["id"] for c in flagged]
        assert cid1 in flagged_ids
        assert cid3 in flagged_ids

    def test_get_flagged_empty(self, repo_db):
        path, _ = repo_db
        assert get_flagged_comments(path=path) == []


class TestSanitizeCommentBody:
    def test_valid_body(self):
        assert sanitize_comment_body("Hello world") == "Hello world"

    def test_strips_whitespace(self):
        assert sanitize_comment_body("  hello  ") == "hello"

    def test_strips_script_tags(self):
        assert sanitize_comment_body("<script>alert('xss')</script>hello") == "alert('xss')hello"

    def test_strips_nested_html(self):
        assert sanitize_comment_body("<div><b>bold</b></div>") == "bold"

    def test_strips_tags_with_attributes(self):
        assert sanitize_comment_body('<a href="evil.com">click</a>') == "click"

    def test_strips_img_tags(self):
        assert sanitize_comment_body('<img src="x.png" onerror="alert(1)">text') == "text"

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError, match="empty"):
            sanitize_comment_body("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError, match="empty"):
            sanitize_comment_body("   \n\t  ")

    def test_rejects_html_only(self):
        with pytest.raises(ValueError, match="empty"):
            sanitize_comment_body("<br><br><img src='x'>")

    def test_rejects_overlength(self):
        with pytest.raises(ValueError, match="exceed"):
            sanitize_comment_body("x" * (MAX_COMMENT_LENGTH + 1))

    def test_max_length_boundary(self):
        body = "a" * MAX_COMMENT_LENGTH
        assert sanitize_comment_body(body) == body

    def test_rejects_non_string(self):
        with pytest.raises(ValueError, match="string"):
            sanitize_comment_body(123)

    def test_preserves_markdown(self):
        md = "## Title\n- item 1\n- item 2\n**bold**"
        assert sanitize_comment_body(md) == md

    def test_preserves_newlines(self):
        body = "line1\nline2\nline3"
        assert sanitize_comment_body(body) == body


class TestAddCommentValidation:
    def test_rejects_empty_body(self, repo_db):
        path, repo_id = repo_db
        with pytest.raises(ValueError, match="empty"):
            add_comment(1, repo_id, "", path=path)

    def test_rejects_whitespace_body(self, repo_db):
        path, repo_id = repo_db
        with pytest.raises(ValueError, match="empty"):
            add_comment(1, repo_id, "   ", path=path)

    def test_rejects_html_only_body(self, repo_db):
        path, repo_id = repo_db
        with pytest.raises(ValueError, match="empty"):
            add_comment(1, repo_id, "<br><img src='x'>", path=path)

    def test_rejects_overlength_body(self, repo_db):
        path, repo_id = repo_db
        with pytest.raises(ValueError, match="exceed"):
            add_comment(1, repo_id, "x" * (MAX_COMMENT_LENGTH + 1), path=path)

    def test_html_stripped_before_save(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "<b>bold</b> text", path=path)
        comments = get_comments(repo_id, path=path)
        assert comments[0]["body"] == "bold text"


class TestUpdateCommentValidation:
    def test_rejects_empty_body(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "Original", path=path)
        with pytest.raises(ValueError, match="empty"):
            update_comment(cid, 1, "", path=path)

    def test_rejects_overlength_body(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "Original", path=path)
        with pytest.raises(ValueError, match="exceed"):
            update_comment(cid, 1, "x" * (MAX_COMMENT_LENGTH + 1), path=path)

    def test_html_stripped_on_update(self, repo_db):
        path, repo_id = repo_db
        cid = add_comment(1, repo_id, "Original", path=path)
        update_comment(cid, 1, "<script>x</script>Updated", path=path)
        comments = get_comments(repo_id, path=path)
        assert comments[0]["body"] == "xUpdated"
