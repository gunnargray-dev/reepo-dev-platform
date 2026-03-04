"""Tests for blog module — CRUD, publish, RSS generation."""
import json
import os
import tempfile

import pytest

from src.db import init_db
from src.community.db import init_community_db
from src.community.blog import (
    create_post, get_post, list_posts, update_post,
    publish_post, generate_rss_feed,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_community_db(path)
    yield path
    os.unlink(path)


class TestCreatePost:
    def test_create_returns_id(self, db_path):
        pid = create_post("hello-world", "Hello World", "Body text", "admin", path=db_path)
        assert pid > 0

    def test_create_with_tags(self, db_path):
        pid = create_post("tagged", "Tagged Post", "Body", "admin",
                          tags=["ai", "python"], path=db_path)
        post = get_post("tagged", path=db_path)
        assert post["tags"] == ["ai", "python"]

    def test_create_without_tags(self, db_path):
        create_post("no-tags", "No Tags", "Body", "admin", path=db_path)
        post = get_post("no-tags", path=db_path)
        assert post["tags"] == []

    def test_create_duplicate_slug_fails(self, db_path):
        create_post("dupe", "First", "Body", "admin", path=db_path)
        with pytest.raises(Exception):
            create_post("dupe", "Second", "Body", "admin", path=db_path)


class TestGetPost:
    def test_get_existing(self, db_path):
        create_post("test-slug", "Test", "Body", "admin", path=db_path)
        post = get_post("test-slug", path=db_path)
        assert post is not None
        assert post["title"] == "Test"
        assert post["slug"] == "test-slug"

    def test_get_nonexistent(self, db_path):
        assert get_post("nonexistent", path=db_path) is None

    def test_get_returns_all_fields(self, db_path):
        create_post("full", "Full Post", "The body", "admin",
                     tags=["tag1"], path=db_path)
        post = get_post("full", path=db_path)
        assert post["slug"] == "full"
        assert post["title"] == "Full Post"
        assert post["body"] == "The body"
        assert post["author"] == "admin"
        assert post["tags"] == ["tag1"]
        assert post["published_at"] is None


class TestListPosts:
    def test_list_published_only(self, db_path):
        create_post("draft", "Draft", "Body", "admin", path=db_path)
        create_post("pub", "Published", "Body", "admin", path=db_path)
        publish_post("pub", path=db_path)
        posts = list_posts(path=db_path)
        assert len(posts) == 1
        assert posts[0]["slug"] == "pub"

    def test_list_empty(self, db_path):
        assert list_posts(path=db_path) == []

    def test_list_with_tag_filter(self, db_path):
        create_post("ai-post", "AI Post", "Body", "admin", tags=["ai"], path=db_path)
        create_post("go-post", "Go Post", "Body", "admin", tags=["go"], path=db_path)
        publish_post("ai-post", path=db_path)
        publish_post("go-post", path=db_path)
        posts = list_posts(tag="ai", path=db_path)
        assert len(posts) == 1
        assert posts[0]["slug"] == "ai-post"

    def test_list_with_limit(self, db_path):
        for i in range(5):
            create_post(f"post-{i}", f"Post {i}", "Body", "admin", path=db_path)
            publish_post(f"post-{i}", path=db_path)
        posts = list_posts(limit=2, path=db_path)
        assert len(posts) == 2

    def test_list_with_offset(self, db_path):
        for i in range(5):
            create_post(f"post-{i}", f"Post {i}", "Body", "admin", path=db_path)
            publish_post(f"post-{i}", path=db_path)
        page1 = list_posts(limit=2, offset=0, path=db_path)
        page2 = list_posts(limit=2, offset=2, path=db_path)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]["slug"] != page2[0]["slug"]


class TestUpdatePost:
    def test_update_title(self, db_path):
        create_post("up", "Original", "Body", "admin", path=db_path)
        assert update_post("up", title="Updated", path=db_path) is True
        post = get_post("up", path=db_path)
        assert post["title"] == "Updated"

    def test_update_body(self, db_path):
        create_post("up", "Title", "Original body", "admin", path=db_path)
        update_post("up", body="New body", path=db_path)
        post = get_post("up", path=db_path)
        assert post["body"] == "New body"

    def test_update_tags(self, db_path):
        create_post("up", "Title", "Body", "admin", tags=["old"], path=db_path)
        update_post("up", tags=["new", "tags"], path=db_path)
        post = get_post("up", path=db_path)
        assert post["tags"] == ["new", "tags"]

    def test_update_no_fields(self, db_path):
        create_post("up", "Title", "Body", "admin", path=db_path)
        assert update_post("up", path=db_path) is False

    def test_update_nonexistent(self, db_path):
        assert update_post("nonexistent", title="X", path=db_path) is False


class TestPublishPost:
    def test_publish(self, db_path):
        create_post("pub", "Publish Me", "Body", "admin", path=db_path)
        assert publish_post("pub", path=db_path) is True
        post = get_post("pub", path=db_path)
        assert post["published_at"] is not None

    def test_publish_already_published(self, db_path):
        create_post("pub", "Title", "Body", "admin", path=db_path)
        publish_post("pub", path=db_path)
        assert publish_post("pub", path=db_path) is False

    def test_publish_nonexistent(self, db_path):
        assert publish_post("nonexistent", path=db_path) is False


class TestGenerateRssFeed:
    def test_rss_structure(self, db_path):
        create_post("rss-test", "RSS Test", "Body text", "admin", path=db_path)
        publish_post("rss-test", path=db_path)
        posts = list_posts(path=db_path)
        rss = generate_rss_feed(posts)
        assert '<?xml version="1.0"' in rss
        assert '<rss version="2.0">' in rss
        assert "<channel>" in rss
        assert "<item>" in rss
        assert "RSS Test" in rss

    def test_rss_empty(self):
        rss = generate_rss_feed([])
        assert "<rss" in rss
        assert "<item>" not in rss

    def test_rss_custom_site_url(self, db_path):
        create_post("url-test", "URL Test", "Body", "admin", path=db_path)
        publish_post("url-test", path=db_path)
        posts = list_posts(path=db_path)
        rss = generate_rss_feed(posts, site_url="https://custom.dev")
        assert "https://custom.dev/blog" in rss

    def test_rss_escapes_html(self):
        posts = [{"title": "A <b>bold</b> title", "slug": "t", "body": "x&y", "author": "a", "published_at": ""}]
        rss = generate_rss_feed(posts)
        assert "&lt;b&gt;" in rss
        assert "&amp;" in rss
