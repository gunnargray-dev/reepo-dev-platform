"""Reepo API — blog endpoints with RSS feed."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter()


class BlogPostCreate(BaseModel):
    slug: str
    title: str
    body: str
    author: str
    tags: list[str] = []


@router.get("/api/blog/rss")
def api_blog_rss():
    from src.server import get_db_path
    from src.community.blog import list_posts, generate_rss_feed

    posts = list_posts(limit=50, path=get_db_path())
    xml = generate_rss_feed(posts)
    return Response(content=xml, media_type="application/rss+xml")


@router.get("/api/blog")
def api_list_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tag: str | None = Query(None),
):
    from src.server import get_db_path
    from src.community.blog import list_posts

    return list_posts(limit=limit, offset=offset, tag=tag, path=get_db_path())


@router.get("/api/blog/{slug}")
def api_get_post(slug: str):
    from src.server import get_db_path
    from src.community.blog import get_post

    post = get_post(slug, path=get_db_path())
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/api/blog")
def api_create_post(data: BlogPostCreate):
    from src.server import get_db_path
    from src.community.blog import create_post

    post_id = create_post(
        slug=data.slug,
        title=data.title,
        body=data.body,
        author=data.author,
        tags=data.tags,
        path=get_db_path(),
    )
    return {"id": post_id, "slug": data.slug}
