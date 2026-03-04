# Reepo.dev

> Open source discovery engine for AI repos. Search, score, save, share.

**Built autonomously by [Awake](https://github.com/gunnargray-dev/Awake).**

## What is Reepo?

Reepo.dev indexes thousands of open source AI repositories — APIs, frameworks, agents, apps, tools, models, datasets, and infrastructure — and scores them on maintenance health, documentation quality, community activity, and more.

Come to Reepo to:
- **Search** — Find the right AI repo for your use case
- **Score** — See quality signals beyond just GitHub stars
- **Save** — Build personal collections of repos you care about
- **Share** — Showcase what you’ve built with open source AI

## Features

- **GitHub Crawler** — Discover AI repos by topic, language, and keyword via GitHub Search API
- **Reepo Score** — Composite 0–100 score: maintenance health, documentation, community signals, tests, license
- **Full-Text Search** — FTS5-powered search with filters, sorting, and highlighted snippets
- **Trending Algorithm** — Star velocity, acceleration, and recency scoring (daily/weekly/monthly)
- **Similar Repos** — Jaccard similarity on topics, category, and star range
- **Comparison Tool (Pro)** — Side-by-side repo comparison across all metrics
- **Export (Pro)** — JSON, CSV, and PDF export of repo data
- **Sponsored Listings** — Labeled placements with sponsor analytics dashboard
- **Newsletter System** — Weekly digest with subscriber management and sponsor slots
- **Stripe Billing** — Pro subscriptions ($9/mo or $79/yr) with feature gates
- **Tiered API Access** — Free/Pro/Enterprise with usage metering
- **Analytics Pipeline** — Page views, search queries, conversion funnel tracking
- **Public Stats Page** — Live index stats, score distributions, growth charts
- **Open Data Export** — Monthly CC-BY-4.0 CSV dump of the full index
- **Contributor Program** — Moderator, contributor, and verified author roles with badges
- **GitHub Action** — Reepo Score CI check for pull requests
- **Responsive Frontend** — React + Vite + Tailwind, mobile-first dark mode UI

## Stack

- **Backend:** Python 3.12+, FastAPI, SQLite (scaling to PostgreSQL)
- **Frontend:** React 18+, Vite, Tailwind CSS
- **Search:** SQLite FTS5
- **Auth:** GitHub OAuth + JWT
- **Payments:** Stripe
- **Cache:** Thread-safe LRU with TTL, warming, and prefix invalidation

## CLI Commands

```
reepo crawl [--topic TOPIC]   Crawl GitHub for AI repos
reepo analyze                  Run analysis pipeline on indexed repos
reepo stats                    Print index statistics
reepo seed                     Populate DB with seed data for development
reepo search QUERY             Search indexed repos (--sort, --limit)
reepo serve [--port 8000]      Start the FastAPI server
reepo newsletter [--json]      Generate newsletter digest
reepo export-data [--output]   Generate open data CSV export
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/search?q=...` | Full-text search with filters |
| `GET /api/repos/{owner}/{name}` | Repo detail with score breakdown |
| `GET /api/repos/{owner}/{name}/similar` | Similar repos |
| `GET /api/categories` | Category listing |
| `GET /api/trending` | Trending repos (daily/weekly/monthly) |
| `GET /api/stats` | Index statistics |
| `GET /api/public-stats` | Public stats page data |
| `GET /api/compare?repos=...` | Side-by-side comparison (Pro) |
| `GET /api/export/{owner}/{name}` | Export repo data (Pro) |
| `GET /api/sponsors` | Active sponsor listings |
| `GET /api/newsletter/latest` | Latest newsletter digest |
| `GET /api/open-data/latest.csv` | Open data CSV download |
| `GET /api/u/{username}/badges` | User contributor badges |
| `GET /api/admin/analytics` | Admin analytics summary |
| `GET /api/health` | Health check |

## Development

```bash
# Clone
git clone https://github.com/gunnargray-dev/reepo-dev-platform.git
cd reepo-dev-platform

# Install
pip install -e ‘.[dev]’

# Run tests
python -m pytest tests/ -q

# Start server
reepo serve

# Seed development data
reepo seed
```

## Project Stats

- **600+** tests across backend modules, API endpoints, and integrations
- **8 phases** of autonomous development (see ROADMAP.md)
- **Zero** human commits — every line written by AI

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full 8-phase product roadmap.

## Session Log

See [SESSION_LOG.md](SESSION_LOG.md) for the autonomous build history.

## License

Open source. See individual module headers for details.
Open data exports are licensed under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

---

*Every line of code in this repo was written by AI. Zero human commits.*
