"""Reepo API — SEO routes: sitemap, robots.txt, OG cards, meta tags."""
from fastapi import APIRouter, HTTPException, Query, Response

router = APIRouter()


@router.get("/sitemap.xml")
def api_sitemap():
    from src.server import get_db_path
    from src.db import list_repos, get_categories
    from src.seo import generate_sitemap_xml

    path = get_db_path()
    repos = list_repos(path=path, limit=5000)
    categories = get_categories(path=path)
    base_url = "https://reepo.dev"
    xml = generate_sitemap_xml(repos, categories, base_url)
    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt")
def api_robots():
    from src.seo import generate_robots_txt

    txt = generate_robots_txt("https://reepo.dev")
    return Response(content=txt, media_type="text/plain")


@router.get("/og/{owner}/{name}.png")
def api_og_card(owner: str, name: str):
    from src.server import get_db_path
    from src.db import get_repo
    from src.og_cards import generate_og_card

    repo = get_repo(owner, name, path=get_db_path())
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    png = generate_og_card(repo)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "max-age=3600"},
    )


@router.get("/api/meta/{page_type}")
def api_meta_tags(
    page_type: str,
    query: str = Query(None),
    count: int = Query(None),
    name: str = Query(None),
    full_name: str = Query(None),
    description: str = Query(None),
    reepo_score: int = Query(None),
    stars: int = Query(None),
    slug: str = Query(None),
    cat_name: str = Query(None),
    cat_description: str = Query(None),
    repo_count: int = Query(None),
):
    from src.seo import generate_meta_tags

    data = {}
    if query is not None:
        data["query"] = query
    if count is not None:
        data["count"] = count
    if name is not None:
        data["name"] = name
    if full_name is not None:
        data["full_name"] = full_name
    if description is not None:
        data["description"] = description
    if reepo_score is not None:
        data["reepo_score"] = reepo_score
    if stars is not None:
        data["stars"] = stars
    if slug is not None:
        data["slug"] = slug
    if cat_name is not None:
        data["name"] = cat_name
    if cat_description is not None:
        data["description"] = cat_description
    if repo_count is not None:
        data["repo_count"] = repo_count

    tags = generate_meta_tags(page_type, data)
    return tags
