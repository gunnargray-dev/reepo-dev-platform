# Reepo.dev — Autonomous Build Rules

## Identity
Reepo.dev is an open source discovery engine for AI repositories. Built autonomously by Awake.

## Repo
- Owner: gunnargray-dev
- Name: reepo-dev-platform
- Branch strategy: feature branches → PR → squash merge to main

## Build Rules
1. One feature per PR, atomic changes.
2. Tests for everything. No PR merges without passing tests. Use pytest.
3. PR descriptions should be detailed and tweet-worthy.
4. Each session = one or more roadmap items checked off.
5. SESSION_LOG.md tracks every session. Append-only.
6. ROADMAP.md is the single source of truth.
7. When the roadmap is complete, add ambitious new items and keep building.
8. Pure Python backend, minimal dependencies. FastAPI for web server. SQLite for storage.
9. React + Vite + Tailwind for frontend. Dark mode default.
10. Never break main. Always run tests before merging.

## Project Structure
```
src/                    # Python backend
  crawler.py            # GitHub repo discovery
  analyzer.py           # Repo scoring pipeline
  taxonomy.py           # Category classification
  db.py                 # Database layer
  search.py             # Full-text search engine
  trending.py           # Trending algorithm
  similar.py            # Similar repos engine
  server.py             # FastAPI application
  api/                  # API route modules
  auth/                 # Auth system (Phase 4)
  collections/          # User collections (Phase 4)
  community/            # Built-with, comments (Phase 5)
  monetization/         # Sponsors, subscriptions (Phase 6)
frontend/               # React + Vite + Tailwind
tests/                  # pytest test suite
data/                   # SQLite DB, seed data
```
