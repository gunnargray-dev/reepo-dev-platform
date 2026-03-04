"""Tests for digest module — generate with mock data, render HTML/markdown."""
import json
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.community.db import init_community_db
from src.community.built_with import submit_project, approve_project
from src.community.digest import (
    generate_digest, render_digest_html, render_digest_markdown, save_digest,
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
def seeded_db(db_path):
    for i in range(12):
        insert_repo({
            "github_id": i + 1, "owner": f"org{i}", "name": f"repo{i}",
            "full_name": f"org{i}/repo{i}", "description": f"Repo number {i}",
            "stars": 1000 * (12 - i), "language": "Python",
            "category_primary": "frameworks",
        }, db_path)
    # Add some Built With projects
    pid1 = submit_project(1, "Cool App", "A cool app", "https://x.com", [1], path=db_path)
    pid2 = submit_project(2, "Nice Tool", "A nice tool", "https://y.com", [2], path=db_path)
    approve_project(pid1, path=db_path)
    approve_project(pid2, path=db_path)
    return db_path


class TestGenerateDigest:
    def test_has_required_keys(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        assert "generated_at" in digest
        assert "trending_repos" in digest
        assert "new_additions" in digest
        assert "top_projects" in digest

    def test_trending_repos_limit(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        assert len(digest["trending_repos"]) <= 10

    def test_new_additions_limit(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        assert len(digest["new_additions"]) <= 5

    def test_top_projects_included(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        assert len(digest["top_projects"]) == 2

    def test_empty_db(self, db_path):
        digest = generate_digest(path=db_path)
        assert digest["trending_repos"] == []
        assert digest["new_additions"] == []
        assert digest["top_projects"] == []


class TestRenderDigestHtml:
    def test_contains_html_tags(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        html = render_digest_html(digest)
        assert "<html>" in html
        assert "</html>" in html
        assert "<h1>" in html

    def test_contains_repo_names(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        html = render_digest_html(digest)
        assert "org0/repo0" in html

    def test_contains_project_titles(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        html = render_digest_html(digest)
        assert "Cool App" in html

    def test_empty_digest_renders(self, db_path):
        digest = generate_digest(path=db_path)
        html = render_digest_html(digest)
        assert "<html>" in html


class TestRenderDigestMarkdown:
    def test_contains_markdown_headers(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        md = render_digest_markdown(digest)
        assert "# Reepo Weekly Digest" in md
        assert "## Trending Repos" in md

    def test_contains_repo_names(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        md = render_digest_markdown(digest)
        assert "org0/repo0" in md

    def test_empty_digest_renders(self, db_path):
        digest = generate_digest(path=db_path)
        md = render_digest_markdown(digest)
        assert "# Reepo Weekly Digest" in md


class TestSaveDigest:
    def test_save_returns_id(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        digest_id = save_digest(digest, path=seeded_db)
        assert digest_id > 0

    def test_sequential_issue_numbers(self, seeded_db):
        d1 = generate_digest(path=seeded_db)
        d2 = generate_digest(path=seeded_db)
        id1 = save_digest(d1, path=seeded_db)
        id2 = save_digest(d2, path=seeded_db)
        assert id2 > id1

    def test_saved_content_is_json(self, seeded_db):
        digest = generate_digest(path=seeded_db)
        save_digest(digest, path=seeded_db)
        from src.db import _connect
        conn = _connect(seeded_db)
        row = conn.execute("SELECT content FROM digest_issues WHERE id = 1").fetchone()
        conn.close()
        parsed = json.loads(row["content"])
        assert "trending_repos" in parsed
