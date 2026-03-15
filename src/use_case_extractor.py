"""Extract specific use cases from repo README and description."""
import asyncio
import base64
import json
import logging
import re
import time

import httpx

from src.db import _connect, DEFAULT_DB_PATH

logger = logging.getLogger(__name__)

# Sections likely to contain use cases / features
FEATURE_HEADINGS = re.compile(
    r"^#{1,3}\s+"
    r"(features|what .* do|use cases|capabilities|highlights|why |"
    r"what is|overview|introduction|about|key features|main features)"
    r".*$",
    re.IGNORECASE | re.MULTILINE,
)

# Match markdown bullet points
BULLET = re.compile(r"^\s*[-*+]\s+(.+)$", re.MULTILINE)

# Match bold/emoji-prefixed feature lines (common in READMEs)
BOLD_FEATURE = re.compile(r"^\s*[-*+]\s+\*\*(.+?)\*\*[:\s-]*(.*)$", re.MULTILINE)

# Patterns that indicate a use case or capability
ACTION_VERBS = re.compile(
    r"\b(build|create|deploy|train|fine-tune|generate|automate|analyze|"
    r"monitor|manage|integrate|convert|extract|process|visualize|"
    r"search|index|stream|serve|host|run|optimize|debug|test|"
    r"orchestrate|schedule|transform|translate|transcribe|detect|"
    r"classify|cluster|segment|annotate|label|evaluate|benchmark|"
    r"chat|converse|summarize|embed|encode|decode|tokenize|parse|"
    r"scrape|crawl|fetch|sync|migrate|export|import|connect|"
    r"authenticate|authorize|cache|queue|scale|load.balance)\b",
    re.IGNORECASE,
)

# Noise phrases to filter out
NOISE = re.compile(
    r"(contributions? welcome|please star|license|install|pip install|"
    r"npm install|docker run|requirements|prerequisites|table of contents|"
    r"acknowledgments|citation|changelog|roadmap|sponsors|"
    r"made with|powered by|built with|special thanks|"
    r"self.host|download|waitlist|join |sign up|subscribe|"
    r"minimum \d|RAM:|GPU:|CPU:|memory:|disk:|"
    r"deprecated|archived|unmaintained|no longer|"
    r"pairing code|legacy:|unknown senders|"
    r"\d+GB|\d+MB|port \d|localhost|127\.0\.0|"
    r"http://|https://|\.com/|\.io/|\.org/|"
    r"use this command|run .*with|to run |to start |"
    r"approve with|^if |^when you |^for more |^to get |^to use |"
    r"founded by|created by|maintained by|developed by|"
    r"^tutorial|^example|^demo|^guide|^docs|^note:|^tip:|"
    r"ubuntu|debian|centos|windows|macos|linux|"
    r"^\d+\+?\s|^\d+k\s|"
    r"ollama|docker compose|kubernetes|helm chart|"
    r"required software|or newer|minimum version|"
    r"^\[x\]|^\[ \]|"
    r"link to |pull request|one pull|choose the right|"
    r"ethical use|content restriction|legal compliance|"
    r"python \(|python \d|node\.?js|"
    r"recommended\)|quickstart|setup |"
    r"^link |read only|previous forum|"
    r"access to required|stable internet|outbound|"
    r"internet connection|ability to make|"
    r"community forum|github issues|email support|best for:|"
    r"submit your|follow the|follow .*on |clean up|before submitting|"
    r"coding style|contributions|architecture & |biology |embedded system|"
    r"codebase$|^\[|"
    r"adjust build|build options|optional\)|"
    r"apply to be|include tests|volunteer|"
    r"amplify them|organize events|"
    r"releases will be|published each|"
    r"development services|"
    r"building the image|build the image|"
    r"^parameters you|saved with that|"
    r"alpha and |sigma$)",
    re.IGNORECASE,
)


def _clean_text(text: str) -> str:
    """Remove markdown formatting, links, images, HTML tags, emojis."""
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)  # images
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links → text
    text = re.sub(r"<[^>]+>", "", text)  # HTML tags
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)  # inline code
    text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)  # bold/italic
    text = re.sub(r"#{1,6}\s+", "", text)  # headings
    # Strip emoji characters (common in READMEs)
    text = re.sub(
        r"[\U0001F300-\U0001F9FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F"
        r"\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF"
        r"\U0000200D\U00002B50\U00002B55\U000023CF\U000023E9-\U000023F3"
        r"\U0000231A\U0000231B]+",
        "", text
    )
    # Strip leading/trailing punctuation like colons, dashes after emoji removal
    text = re.sub(r"^\s*[:\-–—]\s*", "", text)
    return text.strip()


def _extract_feature_sections(readme: str) -> list[str]:
    """Find sections with feature-like headings and extract bullet points."""
    sections = []
    matches = list(FEATURE_HEADINGS.finditer(readme))
    if not matches:
        return sections

    for i, m in enumerate(matches):
        start = m.end()
        # End at next heading or 2000 chars, whichever first
        end = matches[i + 1].start() if i + 1 < len(matches) else start + 2000
        section = readme[start:end]

        # Extract bullets from this section
        for bullet_match in BULLET.finditer(section):
            line = _clean_text(bullet_match.group(1))
            if (len(line) > 15 and len(line) < 200
                    and len(line.split()) >= 4
                    and not NOISE.search(line)):
                sections.append(line)

    return sections


def _extract_from_description(description: str) -> list[str]:
    """Parse description for action-oriented phrases."""
    if not description:
        return []

    results = []
    # Split on common separators
    parts = re.split(r"[.;|/]|\s-\s", description)
    for part in parts:
        part = part.strip()
        if len(part) > 15 and ACTION_VERBS.search(part) and not NOISE.search(part):
            # Capitalize first letter
            results.append(part[0].upper() + part[1:])

    return results


def _extract_first_bullets(readme: str) -> list[str]:
    """Fallback: grab the first meaningful bullets from the README."""
    results = []
    for m in BULLET.finditer(readme[:3000]):
        line = _clean_text(m.group(1))
        if (len(line) > 20 and len(line) < 200
                and len(line.split()) >= 4
                and not NOISE.search(line)):
            results.append(line)
        if len(results) >= 6:
            break
    return results


def _score_use_case(text: str) -> int:
    """Score how good a use case string is (higher = better)."""
    score = 0
    if ACTION_VERBS.search(text):
        score += 5
    if 30 < len(text) < 120:
        score += 2
    if text[0].isupper():
        score += 1
    # Penalize very generic or non-descriptive
    if re.search(r"^(a |an |the |this |it |we |our |see |note|check )", text, re.IGNORECASE):
        score -= 2
    # Penalize very short (likely not a use case)
    if len(text) < 25:
        score -= 2
    # Penalize lines that look like install/setup instructions
    if re.search(r"(^\$|^```|^import |^from |^pip |^npm |^yarn |^brew |^curl )", text):
        score -= 10
    # Penalize lines that are just names/titles without description
    if len(text.split()) <= 3:
        score -= 3
    # Penalize lines with too many special characters (likely code or formatting)
    if len(re.findall(r"[{}()\[\]<>=;|&]", text)) > 2:
        score -= 5
    # Penalize lines that look like navigation/links
    if re.search(r"(click here|learn more|read more|see also|documentation)", text, re.IGNORECASE):
        score -= 5
    # Penalize "support for X" without substance
    if re.search(r"^support for\b", text, re.IGNORECASE) and len(text) < 40:
        score -= 2
    # Bonus for lines that describe what you can do
    if re.search(r"^(build|create|deploy|train|generate|automate|run|use)", text, re.IGNORECASE):
        score += 3
    # Bonus for capability-describing patterns
    if re.search(r"(enables?|allows?|provides?|supports?)\s+(you\s+to\s+)?(\w+ing|\w+tion)", text, re.IGNORECASE):
        score += 3
    # Bonus for specific technical capabilities
    if re.search(r"(real.time|low.latency|high.performance|distributed|parallel|streaming|batch)", text, re.IGNORECASE):
        score += 2
    # Penalize items that are just product/format names (no verb, no description)
    if not re.search(r"\s", text.strip()) or len(text.split()) <= 2:
        score -= 5
    # Penalize items that end abruptly (likely truncated at extraction)
    if text.rstrip()[-1:] not in ".!?)\"'" and len(text) > 60:
        score -= 1
    return score


def extract_use_cases(description: str, readme: str, max_cases: int = 4) -> list[str]:
    """Extract specific use cases from a repo's description and README."""
    candidates: list[str] = []

    # Priority 1: Feature sections in README
    if readme:
        feature_bullets = _extract_feature_sections(readme)
        candidates.extend(feature_bullets)

    # Priority 2: Description parsing
    desc_cases = _extract_from_description(description or "")
    candidates.extend(desc_cases)

    # Priority 3: First bullets from README (fallback)
    if len(candidates) < 2 and readme:
        first_bullets = _extract_first_bullets(readme)
        candidates.extend(first_bullets)

    # Deduplicate (case-insensitive + substring check)
    seen_keys: list[str] = []
    unique = []
    for c in candidates:
        key = c.lower().strip()
        # Skip if exact match or substring of existing
        is_dup = False
        for existing in seen_keys:
            if key == existing or key in existing or existing in key:
                is_dup = True
                break
        if not is_dup:
            seen_keys.append(key)
            unique.append(c)

    # Score and sort
    scored = sorted(unique, key=_score_use_case, reverse=True)

    # Quality filter: skip truncated, too generic, or non-capability items
    filtered = []
    for case in scored:
        # Skip items ending with a single letter followed by nothing (truncated)
        if re.search(r"\s\w$", case) and not case.endswith("."):
            continue
        # Require minimum quality: must contain an action verb OR a capability pattern
        has_action = ACTION_VERBS.search(case)
        has_capability = re.search(
            r"(enables?|allows?|provides?|supports?|powered|driven|native|based|"
            r"compatible|optimized|designed for|built for|works with|"
            r"interface|platform|framework|engine|pipeline|workflow|"
            r"real.time|low.latency|high.performance)",
            case, re.IGNORECASE
        )
        if not has_action and not has_capability and _score_use_case(case) < 3:
            continue
        filtered.append(case)

    # Truncate long ones at word boundary
    result = []
    for case in filtered[:max_cases]:
        if len(case) > 120:
            # Cut at last space before 117 chars
            cut = case[:117].rfind(" ")
            if cut > 60:
                case = case[:cut] + "..."
            else:
                case = case[:117] + "..."
        result.append(case)

    return result


async def fetch_readme(
    owner: str,
    name: str,
    client: httpx.AsyncClient,
    headers: dict,
) -> str | None:
    """Fetch full README content from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{name}/readme"
    try:
        resp = await client.get(url, headers={**headers, "Accept": "application/vnd.github+json"})
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("content", "")
            encoding = data.get("encoding", "")
            if encoding == "base64" and content:
                return base64.b64decode(content).decode("utf-8", errors="replace")
        remaining = int(resp.headers.get("X-RateLimit-Remaining", "100"))
        if remaining <= 2:
            reset_at = int(resp.headers.get("X-RateLimit-Reset", "0"))
            wait = max(reset_at - int(time.time()), 1)
            if wait > 120:
                logger.warning("Rate limit exhausted, reset in %d seconds — stopping", wait)
                return None
            logger.warning("Rate limit low (%d), sleeping %d seconds", remaining, wait)
            await asyncio.sleep(wait)
    except Exception as e:
        logger.debug("Failed to fetch README for %s/%s: %s", owner, name, e)
    return None


async def extract_use_cases_batch(
    db_path: str = DEFAULT_DB_PATH,
    batch_size: int = 100,
    token: str | None = None,
) -> int:
    """Fetch READMEs and extract use cases for repos that don't have them yet."""
    conn = _connect(db_path)

    # Add column if it doesn't exist
    cols = [row[1] for row in conn.execute("PRAGMA table_info(repos)").fetchall()]
    if "use_cases" not in cols:
        conn.execute("ALTER TABLE repos ADD COLUMN use_cases TEXT")
        conn.commit()

    # Get repos without use cases, prioritize by stars
    rows = conn.execute(
        "SELECT id, owner, name, full_name, description FROM repos "
        "WHERE use_cases IS NULL ORDER BY stars DESC LIMIT ?",
        (batch_size,),
    ).fetchall()
    conn.close()

    if not rows:
        logger.info("No repos need use case extraction")
        return 0

    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    processed = 0
    async with httpx.AsyncClient(timeout=15.0) as client:
        for row in rows:
            repo_id = row[0] if isinstance(row, (tuple, list)) else row["id"]
            owner = row[1] if isinstance(row, (tuple, list)) else row["owner"]
            name = row[2] if isinstance(row, (tuple, list)) else row["name"]
            full_name = row[3] if isinstance(row, (tuple, list)) else row["full_name"]
            description = row[4] if isinstance(row, (tuple, list)) else row["description"]

            readme = await fetch_readme(owner, name, client, headers)
            cases = extract_use_cases(description, readme or "")

            conn = _connect(db_path)
            conn.execute(
                "UPDATE repos SET use_cases = ? WHERE id = ?",
                (json.dumps(cases), repo_id),
            )
            # Also update readme_excerpt if we got a fuller one
            if readme and len(readme) > 100:
                excerpt = readme[:2000]
                conn.execute(
                    "UPDATE repos SET readme_excerpt = ? WHERE id = ? AND (readme_excerpt IS NULL OR LENGTH(readme_excerpt) < ?)",
                    (excerpt, repo_id, len(excerpt)),
                )
            conn.commit()
            conn.close()

            processed += 1
            if processed % 50 == 0:
                logger.info("Processed %d/%d repos", processed, len(rows))

    logger.info("Use case extraction complete: %d repos processed", processed)
    return processed
