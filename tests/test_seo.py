"""Tests for SEO module — sitemap, robots.txt, JSON-LD, meta tags, and API endpoints."""
import os
import tempfile
import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

from src.db import init_db, insert_repo
from src.seo import generate_sitemap_xml, generate_robots_txt, generate_jsonld, generate_meta_tags
from src.server import create_app


# --- Unit: generate_sitemap_xml ---

class TestGenerateSitemapXml:
    def test_valid_xml(self):
        repos = [{"owner": "org", "name": "repo"}]
        categories = [{"slug": "frameworks"}]
        xml = generate_sitemap_xml(repos, categories, "https://reepo.dev")
        root = ET.fromstring(xml)
        assert root.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"

    def test_contains_homepage(self):
        xml = generate_sitemap_xml([], [], "https://reepo.dev")
        assert "https://reepo.dev/" in xml

    def test_contains_trending(self):
        xml = generate_sitemap_xml([], [], "https://reepo.dev")
        assert "https://reepo.dev/trending" in xml

    def test_contains_category_pages(self):
        categories = [{"slug": "frameworks"}, {"slug": "agents"}]
        xml = generate_sitemap_xml([], categories, "https://reepo.dev")
        assert "/category/frameworks" in xml
        assert "/category/agents" in xml

    def test_contains_repo_pages(self):
        repos = [{"owner": "org1", "name": "repo1"}, {"owner": "org2", "name": "repo2"}]
        xml = generate_sitemap_xml(repos, [], "https://reepo.dev")
        assert "/repo/org1/repo1" in xml
        assert "/repo/org2/repo2" in xml

    def test_empty_repos_and_categories(self):
        xml = generate_sitemap_xml([], [], "https://reepo.dev")
        root = ET.fromstring(xml)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = root.findall("s:url", ns)
        assert len(urls) == 2  # homepage + trending

    def test_xml_declaration(self):
        xml = generate_sitemap_xml([], [], "https://reepo.dev")
        assert xml.startswith('<?xml version="1.0"')

    def test_escapes_special_chars(self):
        repos = [{"owner": "a&b", "name": "c<d"}]
        xml = generate_sitemap_xml(repos, [], "https://reepo.dev")
        assert "&amp;" in xml
        assert "&lt;" in xml


# --- Unit: generate_robots_txt ---

class TestGenerateRobotsTxt:
    def test_allow_all(self):
        txt = generate_robots_txt("https://reepo.dev")
        assert "User-agent: *" in txt
        assert "Allow: /" in txt

    def test_disallow_admin(self):
        txt = generate_robots_txt("https://reepo.dev")
        assert "Disallow: /api/admin/" in txt

    def test_sitemap_reference(self):
        txt = generate_robots_txt("https://reepo.dev")
        assert "Sitemap: https://reepo.dev/sitemap.xml" in txt


# --- Unit: generate_jsonld ---

class TestGenerateJsonld:
    def test_type_is_software_source_code(self):
        ld = generate_jsonld({"name": "repo", "owner": "org"})
        assert ld["@type"] == "SoftwareSourceCode"

    def test_context(self):
        ld = generate_jsonld({"name": "repo", "owner": "org"})
        assert ld["@context"] == "https://schema.org"

    def test_basic_fields(self):
        repo = {"name": "myrepo", "owner": "org", "url": "https://github.com/org/myrepo"}
        ld = generate_jsonld(repo)
        assert ld["name"] == "myrepo"
        assert ld["codeRepository"] == "https://github.com/org/myrepo"
        assert ld["author"]["name"] == "org"

    def test_optional_fields(self):
        repo = {
            "name": "repo", "owner": "org",
            "description": "A library", "language": "Python",
            "license": "MIT", "stars": 500,
            "category_primary": "frameworks", "created_at": "2024-01-01",
        }
        ld = generate_jsonld(repo)
        assert ld["description"] == "A library"
        assert ld["programmingLanguage"] == "Python"
        assert ld["license"] == "MIT"
        assert ld["interactionStatistic"]["userInteractionCount"] == 500
        assert ld["applicationCategory"] == "frameworks"
        assert ld["dateCreated"] == "2024-01-01"

    def test_missing_optional_fields_excluded(self):
        ld = generate_jsonld({"name": "repo", "owner": "org"})
        assert "description" not in ld
        assert "programmingLanguage" not in ld
        assert "license" not in ld

    def test_stars_zero_included(self):
        ld = generate_jsonld({"name": "repo", "owner": "org", "stars": 0})
        assert "interactionStatistic" in ld
        assert ld["interactionStatistic"]["userInteractionCount"] == 0


# --- Unit: generate_meta_tags ---

class TestGenerateMetaTags:
    def test_home_page(self):
        tags = generate_meta_tags("home")
        assert "Reepo.dev" in tags["title"]
        assert "og:title" in tags
        assert tags["og:type"] == "website"

    def test_search_page(self):
        tags = generate_meta_tags("search", {"query": "transformers", "count": 42})
        assert "transformers" in tags["title"]
        assert "42" in tags["description"]

    def test_repo_detail_page(self):
        tags = generate_meta_tags("repo_detail", {
            "full_name": "org/repo", "description": "A cool repo",
            "reepo_score": 85, "stars": 1000,
        })
        assert "org/repo" in tags["title"]
        assert "85" in tags["title"]
        assert "1000" in tags["description"] or "1,000" in tags["description"]

    def test_category_page(self):
        tags = generate_meta_tags("category", {
            "name": "Frameworks", "description": "ML frameworks",
            "repo_count": 50,
        })
        assert "Frameworks" in tags["title"]
        assert "50" in tags["title"]

    def test_trending_page(self):
        tags = generate_meta_tags("trending")
        assert "Trending" in tags["title"]

    def test_unknown_page_type_fallback(self):
        tags = generate_meta_tags("unknown_page")
        assert "Reepo.dev" in tags["title"]
        assert "og:title" in tags

    def test_all_pages_have_required_keys(self):
        for pt in ["home", "search", "repo_detail", "category", "trending"]:
            tags = generate_meta_tags(pt, {"query": "q", "count": 1, "name": "x",
                                           "full_name": "o/r", "description": "d",
                                           "reepo_score": 50, "stars": 100,
                                           "slug": "s", "repo_count": 5})
            for key in ["title", "description", "og:title", "og:description", "og:type"]:
                assert key in tags, f"Missing {key} for page_type={pt}"


# --- API integration ---

@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app = create_app(path)
    with TestClient(app) as c:
        yield c, path
    os.unlink(path)


@pytest.fixture
def seeded_client(client):
    c, path = client
    insert_repo({
        "github_id": 1, "owner": "org1", "name": "repo1",
        "full_name": "org1/repo1", "description": "A test repo",
        "stars": 1000, "language": "Python", "category_primary": "frameworks",
        "reepo_score": 85,
    }, path)
    return c, path


class TestSitemapAPI:
    def test_get_sitemap_xml(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/sitemap.xml")
        assert resp.status_code == 200
        assert "application/xml" in resp.headers["content-type"]
        assert '<?xml' in resp.text
        assert "/repo/org1/repo1" in resp.text

    def test_sitemap_valid_xml(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/sitemap.xml")
        root = ET.fromstring(resp.text)
        assert root.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"

    def test_sitemap_contains_categories(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/sitemap.xml")
        assert "/category/" in resp.text


class TestRobotsAPI:
    def test_get_robots_txt(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/robots.txt")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        assert "User-agent: *" in resp.text
        assert "Sitemap:" in resp.text


class TestMetaAPI:
    def test_get_meta_home(self, client):
        c, _ = client
        resp = c.get("/api/meta/home")
        assert resp.status_code == 200
        data = resp.json()
        assert "title" in data
        assert "Reepo.dev" in data["title"]

    def test_get_meta_search(self, client):
        c, _ = client
        resp = c.get("/api/meta/search?query=llm&count=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "llm" in data["title"]

    def test_get_meta_repo_detail(self, client):
        c, _ = client
        resp = c.get("/api/meta/repo_detail?full_name=org/repo&reepo_score=90&stars=500")
        assert resp.status_code == 200
        data = resp.json()
        assert "org/repo" in data["title"]

    def test_get_meta_unknown_type(self, client):
        c, _ = client
        resp = c.get("/api/meta/invalid_page")
        assert resp.status_code == 200
        data = resp.json()
        assert "title" in data


class TestOgCardAPI:
    def test_get_og_card_png(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/og/org1/repo1.png")
        assert resp.status_code == 200
        assert "image/png" in resp.headers["content-type"]
        # PNG magic bytes
        assert resp.content[:4] == b'\x89PNG'

    def test_og_card_not_found(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/og/nonexistent/repo.png")
        assert resp.status_code == 404

    def test_og_card_cache_control(self, seeded_client):
        c, _ = seeded_client
        resp = c.get("/og/org1/repo1.png")
        assert "max-age=3600" in resp.headers.get("cache-control", "")
