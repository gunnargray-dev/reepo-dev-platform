"""Reepo CLI — command-line interface for the Reepo platform."""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="reepo",
        description="Reepo.dev — Open source discovery engine for AI repos",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Placeholder subcommands — implemented in later sessions
    subparsers.add_parser("crawl", help="Crawl GitHub for AI repos")
    subparsers.add_parser("analyze", help="Run analysis pipeline on indexed repos")
    subparsers.add_parser("stats", help="Print index statistics")
    subparsers.add_parser("serve", help="Start the FastAPI server")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    print(f"Command '{args.command}' not yet implemented. See ROADMAP.md.")


if __name__ == "__main__":
    main()
