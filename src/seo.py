"""Reepo SEO utilities — sitemap, robots.txt, JSON-LD, and meta tags."""
from datetime import datetime, timezone
from xml.sax.saxutils import escape


def generate_sitemap_xml(repos: list[dict], categories: list[dict], base_url: str) -> str:
    """Generate an XML sitemap for repos and category pages."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = []

    # Homepage
    urls.append(
        f"  <url>\n"
        f"    <loc>{escape(base_url)}/</loc>\n"
        f"    <lastmod>{now}</lastmod>\n"
        f"    <changefreq>daily</changefreq>\n"
        f"    <priority>1.0</priority>\n"
        f"  </url>"
    )

    # Trending page
    urls.append(
        f"  <url>\n"
        f"    <loc>{escape(base_url)}/trending</loc>\n"
        f"    <lastmod>{now}</lastmod>\n"
        f"    <changefreq>daily</changefreq>\n"
        f"    <priority>0.9</priority>\n"
        f"  </url>"
    )

    # Category pages
    for cat in categories:
        slug = cat.get("slug", "")
        urls.append(
            f"  <url>\n"
            f"    <loc>{escape(base_url)}/category/{escape(slug)}</loc>\n"
            f"    <lastmod>{now}</lastmod>\n"
            f"    <changefreq>weekly</changefreq>\n"
            f"    <priority>0.8</priority>\n"
            f"  </url>"
        )

    # Repo detail pages
    for repo in repos:
        owner = escape(repo.get("owner", ""))
        name = escape(repo.get("name", ""))
        urls.append(
            f"  <url>\n"
            f"    <loc>{escape(base_url)}/repo/{owner}/{name}</loc>\n"
            f"    <lastmod>{now}</lastmod>\n"
            f"    <changefreq>weekly</changefreq>\n"
            f"    <priority>0.7</priority>\n"
            f"  </url>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n"
        "</urlset>"
    )


def generate_robots_txt(base_url: str) -> str:
    """Generate robots.txt with sitemap reference."""
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/admin/\n"
        "\n"
        f"Sitemap: {base_url}/sitemap.xml\n"
    )


def generate_jsonld(repo: dict) -> dict:
    """Generate Schema.org SoftwareSourceCode JSON-LD for a repo."""
    ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": repo.get("name", ""),
        "codeRepository": repo.get("url", ""),
        "author": {
            "@type": "Person",
            "name": repo.get("owner", ""),
        },
    }

    if repo.get("description"):
        ld["description"] = repo["description"]
    if repo.get("language"):
        ld["programmingLanguage"] = repo["language"]
    if repo.get("license"):
        ld["license"] = repo["license"]
    if repo.get("stars") is not None:
        ld["interactionStatistic"] = {
            "@type": "InteractionCounter",
            "interactionType": "https://schema.org/LikeAction",
            "userInteractionCount": repo["stars"],
        }
    if repo.get("category_primary"):
        ld["applicationCategory"] = repo["category_primary"]
    if repo.get("created_at"):
        ld["dateCreated"] = repo["created_at"]

    return ld


def generate_meta_tags(page_type: str, data: dict | None = None) -> dict:
    """Generate meta tags (title, description, og:*) for different page types."""
    data = data or {}

    if page_type == "home":
        return {
            "title": "Reepo.dev — AI Open Source Discovery Engine",
            "description": "Discover, compare, and track the best open source AI repositories. Curated scores, trending projects, and category browsing.",
            "og:title": "Reepo.dev — AI Open Source Discovery Engine",
            "og:description": "Discover, compare, and track the best open source AI repositories.",
            "og:type": "website",
        }

    if page_type == "search":
        query = data.get("query", "")
        count = data.get("count", 0)
        return {
            "title": f"Search: {query} — Reepo.dev",
            "description": f"{count} results for '{query}' on Reepo.dev — AI open source discovery.",
            "og:title": f"Search: {query} — Reepo.dev",
            "og:description": f"{count} results for '{query}'.",
            "og:type": "website",
        }

    if page_type == "repo_detail":
        name = data.get("full_name", data.get("name", ""))
        desc = data.get("description", "An open source repository.")
        score = data.get("reepo_score", "")
        stars = data.get("stars", 0)
        return {
            "title": f"{name} — Reepo Score {score} — Reepo.dev",
            "description": f"{desc} — {stars} stars on GitHub.",
            "og:title": f"{name} — Reepo Score {score}",
            "og:description": desc,
            "og:type": "website",
        }

    if page_type == "category":
        cat_name = data.get("name", data.get("slug", ""))
        cat_desc = data.get("description", "")
        count = data.get("repo_count", 0)
        return {
            "title": f"{cat_name} — {count} AI Repos — Reepo.dev",
            "description": f"{cat_desc} Browse {count} curated repositories.",
            "og:title": f"{cat_name} — Reepo.dev",
            "og:description": cat_desc,
            "og:type": "website",
        }

    if page_type == "trending":
        return {
            "title": "Trending AI Repos — Reepo.dev",
            "description": "The hottest open source AI repositories this week. Ranked by Reepo Score.",
            "og:title": "Trending AI Repos — Reepo.dev",
            "og:description": "The hottest open source AI repositories this week.",
            "og:type": "website",
        }

    # Fallback
    return {
        "title": "Reepo.dev",
        "description": "Open source AI repository discovery engine.",
        "og:title": "Reepo.dev",
        "og:description": "Open source AI repository discovery engine.",
        "og:type": "website",
    }
