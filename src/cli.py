"""Reepo CLI — command-line interface for the Reepo platform."""
import argparse
import asyncio
import os
import sys


DEFAULT_DB = "data/reepo.db"


def cmd_crawl(args):
    from src.crawler import crawl_all, crawl_topic

    token = args.token or os.environ.get("GITHUB_TOKEN")

    if args.topic:
        repos = asyncio.run(crawl_topic(args.topic, token=token, db_path=args.db))
        print(f"Crawled topic '{args.topic}': {len(repos)} repos found")
    else:
        count = asyncio.run(crawl_all(token=token, db_path=args.db))
        print(f"Crawl complete: {count} repos indexed")


def cmd_analyze(args):
    from src.analyzer import analyze_all_unscored
    from src.db import init_db

    init_db(args.db)
    count = analyze_all_unscored(args.db)
    print(f"Analyzed {count} repos")


def cmd_stats(args):
    from src.db import (
        init_db,
        count_repos,
        get_repos_by_category,
        get_repos_by_language,
        get_score_stats,
    )

    init_db(args.db)
    total = count_repos(args.db)
    by_category = get_repos_by_category(args.db)
    by_language = get_repos_by_language(args.db, limit=10)
    score_stats = get_score_stats(args.db)

    print(f"Total repos: {total}")
    print()

    if by_category:
        print("Repos by category:")
        for cat, cnt in by_category.items():
            print(f"  {cat}: {cnt}")
        print()

    if by_language:
        print("Top languages:")
        for lang, cnt in by_language.items():
            print(f"  {lang}: {cnt}")
        print()

    if score_stats["avg_score"]:
        print(f"Average Reepo Score: {score_stats['avg_score']}")
        dist = score_stats["distribution"]
        print("Score distribution:")
        print(f"  Excellent (80+): {dist['excellent_80_plus']}")
        print(f"  Good (60-79):    {dist['good_60_79']}")
        print(f"  Fair (40-59):    {dist['fair_40_59']}")
        print(f"  Poor (<40):      {dist['poor_below_40']}")


def cmd_seed(args):
    from src.seed import seed_database

    count = seed_database(args.db)
    print(f"Seeded {count} repos into {args.db}")


def cmd_serve(args):
    import uvicorn
    from src.server import create_app

    create_app(db_path=args.db)
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=args.port,
        reload=False,
    )


def cmd_search(args):
    from src.db import init_db
    from src.search import search, init_fts

    init_db(args.db)
    init_fts(args.db)
    result = search(
        path=args.db,
        query=args.query,
        sort=args.sort,
        page=1,
        per_page=args.limit,
    )

    if not result["results"]:
        print("No results found.")
        return

    print(f"Found {result['total']} results (showing {len(result['results'])}):\n")
    for repo in result["results"]:
        score = repo.get("reepo_score", "?")
        stars = repo.get("stars", 0)
        desc = (repo.get("description") or "")[:80]
        print(f"  [{score}] {repo['full_name']} \u2605{stars}")
        if desc:
            print(f"       {desc}")


def cmd_newsletter(args):
    import json
    from src.db import init_db
    from src.monetization.db import init_monetization_db
    from src.monetization.newsletter import build_weekly_digest

    init_db(args.db)
    init_monetization_db(args.db)
    digest = build_weekly_digest(args.db)

    print(f"=== {digest['title']} ===")
    print(f"Subscribers: {digest['subscriber_count']}\n")

    if digest["trending"]:
        print("Top repos:")
        for repo in digest["trending"]:
            score = repo.get("reepo_score", "?")
            stars = repo.get("stars", 0)
            print(f"  [{score}] {repo['full_name']} \u2605{stars}")
        print()

    if digest["new_repos"]:
        print("New this week:")
        for repo in digest["new_repos"]:
            print(f"  {repo['full_name']} — {repo.get('description', '')[:60]}")
        print()

    if digest["sponsor"]:
        print(f"Sponsor: {digest['sponsor'].get('sponsor_name', 'N/A')}")

    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(digest, indent=2))


def cmd_export_data(args):
    from src.db import init_db
    from src.open_data import generate_open_data_export

    init_db(args.db)
    filepath = generate_open_data_export(args.db, output_dir=args.output)
    print(f"Open data export written to: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        prog="reepo",
        description="Reepo.dev — Open source discovery engine for AI repos",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # crawl
    crawl_parser = subparsers.add_parser("crawl", help="Crawl GitHub for AI repos")
    crawl_parser.add_argument("--topic", type=str, help="Crawl a specific topic")
    crawl_parser.add_argument("--db", type=str, default=DEFAULT_DB, help="Database path")
    crawl_parser.add_argument("--token", type=str, help="GitHub API token")
    crawl_parser.set_defaults(func=cmd_crawl)

    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis pipeline on indexed repos")
    analyze_parser.add_argument("--db", type=str, default=DEFAULT_DB, help="Database path")
    analyze_parser.set_defaults(func=cmd_analyze)

    # stats
    stats_parser = subparsers.add_parser("stats", help="Print index statistics")
    stats_parser.add_argument("--db", type=str, default=DEFAULT_DB, help="Database path")
    stats_parser.set_defaults(func=cmd_stats)

    # seed
    seed_parser = subparsers.add_parser("seed", help="Populate DB with seed data for development")
    seed_parser.add_argument("--db", type=str, default=DEFAULT_DB, help="Database path")
    seed_parser.set_defaults(func=cmd_seed)

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the FastAPI server")
    serve_parser.add_argument("--db", type=str, default=DEFAULT_DB, help="Database path")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    serve_parser.set_defaults(func=cmd_serve)

    # search
    search_parser = subparsers.add_parser("search", help="Search indexed repos")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument("--db", type=str, default=DEFAULT_DB, help="Database path")
    search_parser.add_argument("--sort", type=str, default="relevance", help="Sort: relevance, stars, score, newest")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")
    search_parser.set_defaults(func=cmd_search)

    # newsletter
    newsletter_parser = subparsers.add_parser("newsletter", help="Generate newsletter digest")
    newsletter_parser.add_argument("--db", type=str, default=DEFAULT_DB, help="Database path")
    newsletter_parser.add_argument("--json", action="store_true", help="Output raw JSON")
    newsletter_parser.set_defaults(func=cmd_newsletter)

    # export-data
    export_parser = subparsers.add_parser("export-data", help="Generate open data CSV export")
    export_parser.add_argument("--db", type=str, default=DEFAULT_DB, help="Database path")
    export_parser.add_argument("--output", type=str, default="data", help="Output directory")
    export_parser.set_defaults(func=cmd_export_data)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
    else:
        print(f"Command '{args.command}' not yet implemented. See ROADMAP.md.")


if __name__ == "__main__":
    main()
