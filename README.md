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

## Stack

- **Backend:** Python 3.12+, FastAPI, SQLite (scaling to PostgreSQL)
- **Frontend:** React 18+, Vite, Tailwind CSS
- **Search:** SQLite FTS5
- **Auth:** GitHub OAuth + JWT
- **Payments:** Stripe

## Development

```bash
# Clone
git clone https://github.com/gunnargray-dev/reepo-dev-platform.git
cd reepo-dev-platform

# Install
pip install -e '.[dev]'

# Run tests
python -m pytest tests/ -q

# Start server (once built)
reepo serve
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full 8-phase product roadmap.

## Session Log

See [SESSION_LOG.md](SESSION_LOG.md) for the autonomous build history.

---

*Every line of code in this repo was written by AI. Zero human commits.*
