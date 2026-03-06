"""Reepo bot core — command parsing, execution, and response formatting."""
import re

from src.db import DEFAULT_DB_PATH


def parse_command(text: str) -> dict:
    """Parse a bot command string into a structured dict.

    Supported commands:
        /reepo search <query>
        /reepo info <owner/name>
        /reepo trending [category]
        /reepo compare <owner/name> <owner/name>
        /reepo categories
        /reepo help
    """
    text = text.strip()
    # Strip leading /reepo prefix if present
    if text.lower().startswith("/reepo"):
        text = text[6:].strip()

    if not text:
        return {"command": "help"}

    parts = text.split(None, 1)
    cmd = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "search":
        if not args:
            return {"command": "error", "message": "Usage: /reepo search <query>"}
        return {"command": "search", "query": args}

    if cmd == "info":
        if not args or "/" not in args:
            return {"command": "error", "message": "Usage: /reepo info <owner/name>"}
        owner, name = args.split("/", 1)
        return {"command": "info", "owner": owner.strip(), "name": name.strip()}

    if cmd == "trending":
        if args:
            return {"command": "trending", "category": args.strip()}
        return {"command": "trending", "category": None}

    if cmd == "compare":
        repos = re.findall(r"[\w.\-]+/[\w.\-]+", args)
        if len(repos) < 2:
            return {"command": "error", "message": "Usage: /reepo compare <owner/name> <owner/name>"}
        return {"command": "compare", "repos": repos[:2]}

    if cmd == "categories":
        return {"command": "categories"}

    if cmd == "help":
        return {"command": "help"}

    return {"command": "unknown", "text": text}


def execute_command(parsed: dict, db_path: str = DEFAULT_DB_PATH) -> dict:
    """Execute a parsed command against the database."""
    cmd = parsed.get("command")

    if cmd == "help":
        return {
            "command": "help",
            "text": (
                "*Reepo Bot Commands*\n"
                "• `/reepo search <query>` — Search AI repos\n"
                "• `/reepo info <owner/name>` — Repo details\n"
                "• `/reepo trending [category]` — Trending repos\n"
                "• `/reepo compare <a> <b>` — Compare two repos\n"
                "• `/reepo categories` — List categories\n"
                "• `/reepo help` — Show this help"
            ),
        }

    if cmd == "error":
        return {"command": "error", "text": parsed.get("message", "Invalid command")}

    if cmd == "unknown":
        return {
            "command": "error",
            "text": f"Unknown command: {parsed.get('text', '')}. Try `/reepo help`.",
        }

    if cmd == "search":
        from src.search import search
        results = search(path=db_path, query=parsed["query"], per_page=5)
        repos = results.get("results", [])
        return {
            "command": "search",
            "query": parsed["query"],
            "total": results.get("total", 0),
            "repos": [
                {
                    "full_name": r.get("full_name", ""),
                    "description": r.get("description", ""),
                    "stars": r.get("stars", 0),
                    "reepo_score": r.get("reepo_score"),
                    "url": r.get("url", ""),
                }
                for r in repos
            ],
        }

    if cmd == "info":
        from src.db import get_repo
        repo = get_repo(parsed["owner"], parsed["name"], path=db_path)
        if not repo:
            return {
                "command": "error",
                "text": f"Repo `{parsed['owner']}/{parsed['name']}` not found.",
            }
        return {
            "command": "info",
            "repo": {
                "full_name": repo.get("full_name", ""),
                "description": repo.get("description", ""),
                "stars": repo.get("stars", 0),
                "forks": repo.get("forks", 0),
                "language": repo.get("language", ""),
                "reepo_score": repo.get("reepo_score"),
                "category": repo.get("category_primary", ""),
                "url": repo.get("url", ""),
                "license": repo.get("license", ""),
            },
        }

    if cmd == "trending":
        from src.trending import get_trending
        repos = get_trending(path=db_path, limit=5)
        if parsed.get("category"):
            repos = [r for r in repos if r.get("category_primary") == parsed["category"]]
        return {
            "command": "trending",
            "category": parsed.get("category"),
            "repos": [
                {
                    "full_name": r.get("full_name", ""),
                    "stars": r.get("stars", 0),
                    "star_delta": r.get("star_delta", 0),
                    "reepo_score": r.get("reepo_score"),
                }
                for r in repos[:5]
            ],
        }

    if cmd == "compare":
        from src.db import get_repo
        repos = []
        for ref in parsed["repos"]:
            owner, name = ref.split("/", 1)
            repo = get_repo(owner, name, path=db_path)
            if repo:
                repos.append({
                    "full_name": repo.get("full_name", ""),
                    "stars": repo.get("stars", 0),
                    "forks": repo.get("forks", 0),
                    "reepo_score": repo.get("reepo_score"),
                    "language": repo.get("language", ""),
                })
        if len(repos) < 2:
            return {"command": "error", "text": "One or both repos not found."}
        return {"command": "compare", "repos": repos}

    if cmd == "categories":
        from src.db import get_categories
        cats = get_categories(path=db_path)
        return {
            "command": "categories",
            "categories": [
                {"name": c.get("name", ""), "slug": c.get("slug", ""), "repo_count": c.get("repo_count", 0)}
                for c in cats
            ],
        }

    return {"command": "error", "text": "Unknown command."}


def format_slack_response(result: dict) -> dict:
    """Format a command result as a Slack Block Kit message."""
    cmd = result.get("command")
    blocks = []

    if cmd == "help" or cmd == "error":
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": result.get("text", "")},
        })

    elif cmd == "search":
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"🔍 *Search results for '{result['query']}'* ({result['total']} total)"},
        })
        for repo in result.get("repos", []):
            score = repo.get("reepo_score") or "N/A"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{repo['full_name']}* — Score: {score} ⭐ {repo['stars']}\n{repo.get('description', '')}",
                },
            })

    elif cmd == "info":
        repo = result["repo"]
        score = repo.get("reepo_score") or "N/A"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{repo['full_name']}*\n"
                    f"{repo.get('description', '')}\n\n"
                    f"⭐ {repo['stars']} | 🍴 {repo['forks']} | Score: {score}\n"
                    f"Language: {repo.get('language', 'N/A')} | License: {repo.get('license', 'N/A')}\n"
                    f"Category: {repo.get('category', 'N/A')}"
                ),
            },
        })

    elif cmd == "trending":
        cat = result.get("category") or "all"
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"🔥 *Trending repos* ({cat})"},
        })
        for repo in result.get("repos", []):
            score = repo.get("reepo_score") or "N/A"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{repo['full_name']}* — ⭐ {repo['stars']} (+{repo.get('star_delta', 0)}) Score: {score}",
                },
            })
        if not result.get("repos"):
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "No trending repos found."},
            })

    elif cmd == "compare":
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "⚖️ *Repo Comparison*"},
        })
        for repo in result.get("repos", []):
            score = repo.get("reepo_score") or "N/A"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{repo['full_name']}* — ⭐ {repo['stars']} | 🍴 {repo['forks']} | Score: {score} | {repo.get('language', '')}",
                },
            })

    elif cmd == "categories":
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "📂 *Categories*"},
        })
        lines = [f"• *{c['name']}* (`{c['slug']}`) — {c['repo_count']} repos" for c in result.get("categories", [])]
        if lines:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n".join(lines)},
            })

    if not blocks:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "No results."},
        })

    return {"response_type": "in_channel", "blocks": blocks}


def format_discord_response(result: dict) -> dict:
    """Format a command result as a Discord embed message."""
    cmd = result.get("command")

    if cmd == "help" or cmd == "error":
        return {
            "type": 4,
            "data": {
                "embeds": [{
                    "title": "Reepo Bot" if cmd == "help" else "Error",
                    "description": result.get("text", ""),
                    "color": 0x38bdf8 if cmd == "help" else 0xe05d44,
                }],
            },
        }

    if cmd == "search":
        desc_lines = []
        for repo in result.get("repos", []):
            score = repo.get("reepo_score") or "N/A"
            desc_lines.append(f"**{repo['full_name']}** — Score: {score} ⭐ {repo['stars']}")
        return {
            "type": 4,
            "data": {
                "embeds": [{
                    "title": f"Search: {result['query']} ({result['total']} results)",
                    "description": "\n".join(desc_lines) or "No results found.",
                    "color": 0x38bdf8,
                }],
            },
        }

    if cmd == "info":
        repo = result["repo"]
        score = repo.get("reepo_score") or "N/A"
        return {
            "type": 4,
            "data": {
                "embeds": [{
                    "title": repo["full_name"],
                    "description": repo.get("description", ""),
                    "color": 0x38bdf8,
                    "fields": [
                        {"name": "Stars", "value": str(repo["stars"]), "inline": True},
                        {"name": "Forks", "value": str(repo["forks"]), "inline": True},
                        {"name": "Score", "value": str(score), "inline": True},
                        {"name": "Language", "value": repo.get("language") or "N/A", "inline": True},
                        {"name": "License", "value": repo.get("license") or "N/A", "inline": True},
                        {"name": "Category", "value": repo.get("category") or "N/A", "inline": True},
                    ],
                }],
            },
        }

    if cmd == "trending":
        cat = result.get("category") or "all"
        desc_lines = []
        for repo in result.get("repos", []):
            score = repo.get("reepo_score") or "N/A"
            desc_lines.append(f"**{repo['full_name']}** ⭐ {repo['stars']} (+{repo.get('star_delta', 0)}) Score: {score}")
        return {
            "type": 4,
            "data": {
                "embeds": [{
                    "title": f"Trending Repos ({cat})",
                    "description": "\n".join(desc_lines) or "No trending repos found.",
                    "color": 0xff6b35,
                }],
            },
        }

    if cmd == "compare":
        desc_lines = []
        for repo in result.get("repos", []):
            score = repo.get("reepo_score") or "N/A"
            desc_lines.append(f"**{repo['full_name']}** — ⭐ {repo['stars']} | Forks: {repo['forks']} | Score: {score} | {repo.get('language', '')}")
        return {
            "type": 4,
            "data": {
                "embeds": [{
                    "title": "Repo Comparison",
                    "description": "\n".join(desc_lines),
                    "color": 0x38bdf8,
                }],
            },
        }

    if cmd == "categories":
        lines = [f"**{c['name']}** (`{c['slug']}`) — {c['repo_count']} repos" for c in result.get("categories", [])]
        return {
            "type": 4,
            "data": {
                "embeds": [{
                    "title": "Categories",
                    "description": "\n".join(lines) or "No categories.",
                    "color": 0x38bdf8,
                }],
            },
        }

    return {"type": 4, "data": {"embeds": [{"title": "Reepo", "description": "No results.", "color": 0x38bdf8}]}}


def format_plain_response(result: dict) -> str:
    """Format a command result as plain text."""
    cmd = result.get("command")

    if cmd == "help" or cmd == "error":
        return result.get("text", "")

    if cmd == "search":
        lines = [f"Search: {result['query']} ({result['total']} results)"]
        for repo in result.get("repos", []):
            score = repo.get("reepo_score") or "N/A"
            lines.append(f"  {repo['full_name']} — Score: {score}, Stars: {repo['stars']}")
        return "\n".join(lines)

    if cmd == "info":
        repo = result["repo"]
        score = repo.get("reepo_score") or "N/A"
        return (
            f"{repo['full_name']}\n"
            f"{repo.get('description', '')}\n"
            f"Stars: {repo['stars']} | Forks: {repo['forks']} | Score: {score}\n"
            f"Language: {repo.get('language', 'N/A')} | License: {repo.get('license', 'N/A')}"
        )

    if cmd == "trending":
        cat = result.get("category") or "all"
        lines = [f"Trending ({cat}):"]
        for repo in result.get("repos", []):
            score = repo.get("reepo_score") or "N/A"
            lines.append(f"  {repo['full_name']} — Stars: {repo['stars']} (+{repo.get('star_delta', 0)}), Score: {score}")
        return "\n".join(lines)

    if cmd == "compare":
        lines = ["Comparison:"]
        for repo in result.get("repos", []):
            score = repo.get("reepo_score") or "N/A"
            lines.append(f"  {repo['full_name']} — Stars: {repo['stars']}, Forks: {repo['forks']}, Score: {score}")
        return "\n".join(lines)

    if cmd == "categories":
        lines = ["Categories:"]
        for c in result.get("categories", []):
            lines.append(f"  {c['name']} ({c['slug']}) — {c['repo_count']} repos")
        return "\n".join(lines)

    return "No results."
