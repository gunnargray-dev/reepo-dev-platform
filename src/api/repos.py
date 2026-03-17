"""Reepo API — repo routes."""
import base64
import re
import httpx
from fastapi import APIRouter, HTTPException, Query

from src.db import get_repo, list_repos, count_repos, _connect
from src.similar import find_similar
from src.middleware import detail_cache

router = APIRouter()

# Lines to skip entirely
_SKIP_LINE = re.compile(
    r"(^\s*[-*+]\s|"                    # bullet points
    r"^\s*\d+\.\s|"                     # numbered lists
    r"^>\s|"                            # blockquotes
    r"^\|.*\||"                         # tables
    r"^[-=]{3,}$|"                      # horizontal rules
    r"^```|"                            # code blocks
    r"^\[!|"                            # GitHub alerts
    r"^!?\[|"                           # images and links at line start
    r"^<|"                              # HTML tags
    r"^<!--|"                           # comments
    r"^Copyright|"                      # copyright notices
    r"^Licensed under)"                 # license text
)

_NOISE_CONTENT = re.compile(
    r"(translations?\.?\s|deutsch|español|français|日本語|한국어|中文|русский|"
    r"português|العربية|हिन्दी|"
    r"self.host|waitlist|join the|sign up|subscribe|join our team|"
    r"getting started|quick start|how to install|"
    r"system requirements|hardware requirements|prerequisites|"
    r"table of contents|contributing|acknowledgments|"
    r"follow .*on |discord\.gg|twitter\.com|telegram|"
    r"\bNOTE\b|\bWARNING\b|"
    r"npx |npm |pip |brew |docker run|curl |wget |"
    r"requires? (?:node|python|docker)|"
    r"try .* instantly|"
    r"passionate about|hiring|careers|"
    r"src=|href=|\.png|\.svg|\.gif|"
    r"all rights reserved|apache license|mit license|"
    r"polyform|licensed under|this .* is licensed|"
    r"see .*for the full list|"
    r"grateful .* support|sponsors|"
    r"easy way for ai agents|through the cli$|"
    r"can be installed using|before proceeding|"
    r"you'll be prompted|connect .* to your|"
    r"see the full .* documentation|all available commands|"
    r"want to skip|skip the setup|use our cloud|"
    r"backward compatible api for$|"
    r"want to learn more|check out our|documentation for|"
    r"get up and running with|"
    r"create environment and|"
    r"strives to abide|best practices in open.source|"
    r"^\d+\.\s+\w+|"
    r"this creates a |available templates|working example|"
    r"^for machine learning\. it has)",
    re.IGNORECASE,
)

# Patterns that indicate a real project description
_DESCRIPTION_SIGNAL = re.compile(
    r"\b(is a |is an |provides |enables |allows |makes it |designed to |"
    r"helps you |lets you |platform for |framework for |library for |"
    r"tool for |toolkit for |engine for |solution for |"
    r"open.source |that (?:can|lets|helps|enables|allows|makes)|"
    r"used to |built for |built to |written in )\b",
    re.IGNORECASE,
)


def _clean_markdown_line(text: str) -> str:
    """Strip markdown formatting from a single line."""
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url) -> text
    text = re.sub(r'<[^>]+>', '', text)                     # HTML tags
    text = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', text)     # bold/italic
    text = re.sub(r'[`~]+', '', text)                       # code/strikethrough
    text = re.sub(r'&nbsp;', ' ', text)                     # html entities
    text = re.sub(r'\s+', ' ', text)                        # collapse whitespace
    return text.strip()


def _extract_readme_excerpt(content: str) -> str:
    """Extract a clean introductory description from README markdown."""
    lines = content.split("\n")
    paragraphs: list[str] = []
    current: list[str] = []
    in_code_block = False

    for line in lines[:150]:  # Only scan first ~150 lines
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if in_code_block:
            continue

        # Headings break paragraphs
        if stripped.startswith("#"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue

        # Empty line = paragraph break
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue

        # Skip non-prose lines
        if _SKIP_LINE.match(stripped):
            continue

        cleaned = _clean_markdown_line(stripped)
        if not cleaned or len(cleaned) < 10:
            continue

        current.append(cleaned)

    if current:
        paragraphs.append(" ".join(current))

    # Score each paragraph and pick the best one
    best = ""
    best_score = -1

    for para in paragraphs:
        if _NOISE_CONTENT.search(para):
            continue
        if len(para) < 30:
            continue

        score = 0
        # Strong signal: contains "is a", "provides", "framework for", etc.
        if _DESCRIPTION_SIGNAL.search(para):
            score += 10
        # Prefer longer paragraphs (more informative)
        score += min(len(para) // 30, 5)
        # Prefer paragraphs with multiple sentences
        score += min(para.count(". "), 3)
        # Penalize very long paragraphs (likely grabbed too much)
        if len(para) > 800:
            score -= 3

        if score > best_score:
            best_score = score
            best = para

    if not best or best_score < 3:
        return ""

    # Trim to ~500 chars at sentence boundary
    if len(best) > 500:
        cut = best[:500].rfind(". ")
        if cut > 200:
            return best[:cut + 1]
        return best[:497] + "..."
    return best


@router.get("/api/repos")
def api_list_repos(
    category: str | None = Query(None),
    language: str | None = Query(None),
    min_score: int | None = Query(None, ge=0, le=100),
    sort_by: str = Query("stars"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    from src.server import get_db_path

    db_path = get_db_path()
    repos = list_repos(
        path=db_path, category=category, language=language,
        min_score=min_score, sort_by=sort_by, limit=limit, offset=offset,
    )
    total = count_repos(db_path)
    return {"repos": repos, "total": total}


@router.get("/api/repos/{owner}/{name}")
def api_get_repo(owner: str, name: str):
    from src.server import get_db_path

    db_path = get_db_path()

    cache_key = detail_cache.make_key("repo", owner=owner, name=name)
    cached = detail_cache.get(cache_key)
    if cached is not None:
        return cached

    repo = get_repo(owner, name, db_path)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    from src.monetization.affiliates import get_affiliate_link
    affiliate = get_affiliate_link(repo["id"], path=db_path)
    if affiliate:
        repo["affiliate_link"] = {
            "provider": affiliate["provider"],
            "url": affiliate["url"],
            "link_id": affiliate["id"],
        }

    detail_cache.set(cache_key, repo, ttl=900)
    return repo


@router.get("/api/repos/{owner}/{name}/readme")
async def api_repo_readme(owner: str, name: str):
    """Get the README excerpt for a repo. Fetches from GitHub if not cached."""
    from src.server import get_db_path

    db_path = get_db_path()
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT readme_excerpt FROM repos WHERE owner = ? AND name = ?",
        (owner, name),
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Repo not found")

    excerpt = row[0] if isinstance(row, (tuple, list)) else row["readme_excerpt"]
    if excerpt:
        conn.close()
        return {"readme": excerpt}

    # Fetch from GitHub API
    url = f"https://api.github.com/repos/{owner}/{name}/readme"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"Accept": "application/vnd.github+json"})
            if resp.status_code == 200:
                data = resp.json()
                content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
                excerpt = _extract_readme_excerpt(content)
                if not excerpt:
                    # Fall back to repo description from DB
                    desc_row = conn.execute(
                        "SELECT description FROM repos WHERE owner = ? AND name = ?",
                        (owner, name),
                    ).fetchone()
                    if desc_row:
                        excerpt = desc_row["description"] or ""
                # Cache in DB
                conn.execute(
                    "UPDATE repos SET readme_excerpt = ? WHERE owner = ? AND name = ?",
                    (excerpt, owner, name),
                )
                conn.commit()
                conn.close()
                return {"readme": excerpt}
    except Exception:
        pass

    conn.close()
    return {"readme": None}


@router.get("/api/repos/{owner}/{name}/similar")
def api_similar_repos(
    owner: str,
    name: str,
    limit: int = Query(10, ge=1, le=50),
):
    from src.server import get_db_path

    db_path = get_db_path()
    results = find_similar(db_path, owner, name, limit=limit)
    return {"results": results, "total": len(results)}
