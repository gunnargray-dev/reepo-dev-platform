# Reepo.dev — Product Roadmap

> Open source discovery engine for AI repos. Built autonomously by [Awake](https://github.com/gunnargray-dev/Awake).

**Repo:** `gunnargray-dev/reepo-dev-platform`
**Domain:** reepo.dev
**Stack:** Python backend (FastAPI), React frontend (Vite + Tailwind), SQLite → PostgreSQL, GitHub API

---

## Phase 1 — Data Engine (Sessions 0–3)

The foundation. Crawl, index, analyze, and store open source AI repos at scale.

- [x] **Project initialization** — Repo structure, roadmap, rules, session log, pyproject.toml, test framework
- [x] **GitHub crawler** — Discover AI repos by topic tags, language, and keyword search via GitHub Search API. Rate-limit aware with exponential backoff.
- [x] **Category taxonomy** — Define and assign categories. LLM classification on repo description + README excerpt for auto-categorization.
- [x] **Repo analyzer pipeline** — Maintenance health, documentation quality, community signals, test presence, license type. Composite Reepo Score (0–100).
- [x] **SQLite data store** — repos, score_history, categories tables with proper indexes.
- [x] **CLI commands** — `reepo crawl`, `reepo analyze`, `reepo stats`
- [x] **Seed batch** — Crawl and analyze initial 500+ AI repos across all categories.
- [x] Tests for all modules (target: 150+ tests)

---

## Phase 2 — Search & API (Sessions 4–7)

- [x] **Full-text search engine** — SQLite FTS5 index with filters and highlighted snippets
- [x] **FastAPI server** — GET /api/search, /api/repos/{owner}/{name}, /api/categories, /api/trending, /api/stats, /api/repos/{owner}/{name}/similar
- [x] **Trending algorithm** — Star velocity, acceleration, recency scoring
- [x] **Similar repos engine** — Jaccard similarity on topics, category, star range
- [x] **API rate limiting & caching** — Per-IP rate limiting, TTL cache, ETag support
- [x] **OpenAPI spec** — Auto-generated docs at /api/docs
- [x] Tests (target: 250+ total) — 1329 tests passing

---

## Phase 3 — Web Frontend (Sessions 8–14)

- [x] **Landing page** — Search bar, category grid, trending carousel, dark mode
- [x] **Search results page** — Filterable sidebar, repo cards with Reepo Score badges
- [x] **Repo detail page** — Score breakdown, README preview, similar repos, share button
- [x] **Category browse pages** — /category/{slug}
- [x] **Trending page** — Daily/weekly/monthly tabs
- [x] **SEO infrastructure** — SSR/pre-rendering, OG tags, sitemap, structured data
- [x] **OG share cards** — Dynamic 1200×630 PNG per repo
- [x] **Responsive design** — Mobile-first
- [x] Tests (target: 350+ total) — 1329 tests passing

---

## Phase 4 — User Accounts & Collections (Sessions 15–20)

- [x] **Auth system** — GitHub OAuth, JWT tokens
- [x] **Collections** — Named, public/private saved lists of repos
- [x] **Bookmarks** — Quick-save repos
- [x] **User profile pages** — /u/{username}
- [x] **Follow system** — Lightweight social layer
- [x] **Notifications** — In-app + email digest
- [x] **API keys** — User-generated keys with usage tracking
- [ ] **PostgreSQL migration**
- [x] Tests (target: 500+ total) — 1329 tests passing

---

## Phase 5 — Community & "Built With" Showcase (Sessions 21–26)

- [x] **"Built With" submissions** — User-submitted projects using indexed repos
- [x] **Upvotes** — Community curation
- [x] **Comments** — Threaded, markdown, moderated
- [x] **Weekly digest** — Auto-generated newsletter + blog post + RSS
- [x] **Submit a repo** — User-suggested repo additions
- [x] **Admin dashboard** — Moderation, user mgmt, index health
- [x] **Blog / content pages** — SEO articles from index data
- [x] Tests (target: 650+ total) — 1329 tests passing

---

## Phase 6 — Monetization Infrastructure (Sessions 27–32)

- [x] **Sponsored listings** — Labeled placements + sponsor analytics dashboard
- [x] **Stripe integration** — Pro subscriptions ($9/mo or $79/yr)
- [x] **Pro feature gates** — Unlimited collections, comparison tool, export, no ads
- [x] **Comparison tool (Pro)** — Side-by-side repo comparison
- [x] **Export (Pro)** — JSON/CSV/PDF export
- [x] **Affiliate link system** — "Try hosted version" buttons with tracking
- [x] **Newsletter sponsorship** — Subscriber mgmt, sponsor slots, booking system
- [x] **Tiered API access** — Free/Pro/Enterprise with usage metering
- [x] Tests (target: 800+ total) — 1329 tests passing

---

## Phase 7 — Growth & Retention (Sessions 33–38)

- [x] **Automated daily crawl** — Discover + re-analyze repos on schedule
- [ ] **GitHub App** — Real-time updates from repo owners
- [x] **Embeddable badges** — SVG Reepo Score badges for READMEs
- [ ] **Chrome extension** — Reepo Score overlay on GitHub
- [x] **Awesome List import** — Bulk-import from awesome-* repos
- [x] **Personalized recommendations** — Collaborative filtering
- [x] **Changelog tracking** — Per-repo timeline of notable changes
- [ ] **i18n** — Mandarin, Japanese, Spanish, Portuguese, Korean
- [x] Tests (target: 950+ total) — 1329 tests passing

---

## Phase 8 — Platform Maturity (Sessions 39+)

- [x] **Performance optimization** — Thread-safe LRU cache with TTL, warming, prefix invalidation
- [x] **Analytics pipeline** — Page views, search queries, conversion funnel
- [x] **Public stats page** — /stats with index growth over time
- [x] **Contributor program** — Community moderators, contributors, verified authors with badges
- [x] **Slack / Discord bot** — Search Reepo from chat
- [x] **Reepo Score CI** — GitHub Action for PR checks
- [x] **Open data export** — Monthly CC-BY CSV dump
- [x] Tests — 1329 tests passing
