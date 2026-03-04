# Reepo.dev — Product Roadmap

> Open source discovery engine for AI repos. Built autonomously by [Awake](https://github.com/gunnargray-dev/Awake).

**Repo:** `gunnargray-dev/reepo-dev-platform`
**Domain:** reepo.dev
**Stack:** Python backend (FastAPI), React frontend (Vite + Tailwind), SQLite → PostgreSQL, GitHub API

---

## Phase 1 — Data Engine (Sessions 0–3)

The foundation. Crawl, index, analyze, and store open source AI repos at scale.

- [x] **Project initialization** — Repo structure, roadmap, rules, session log, pyproject.toml, test framework
- [ ] **GitHub crawler** — Discover AI repos by topic tags, language, and keyword search via GitHub Search API. Rate-limit aware with exponential backoff.
- [ ] **Category taxonomy** — Define and assign categories. LLM classification on repo description + README excerpt for auto-categorization.
- [ ] **Repo analyzer pipeline** — Maintenance health, documentation quality, community signals, test presence, license type. Composite Reepo Score (0–100).
- [ ] **SQLite data store** — repos, score_history, categories tables with proper indexes.
- [ ] **CLI commands** — `reepo crawl`, `reepo analyze`, `reepo stats`
- [ ] **Seed batch** — Crawl and analyze initial 500+ AI repos across all categories.
- [ ] Tests for all modules (target: 150+ tests)

---

## Phase 2 — Search & API (Sessions 4–7)

- [ ] **Full-text search engine** — SQLite FTS5 index with filters and highlighted snippets
- [ ] **FastAPI server** — GET /api/search, /api/repos/{owner}/{name}, /api/categories, /api/trending, /api/stats, /api/repos/{owner}/{name}/similar
- [ ] **Trending algorithm** — Star velocity, acceleration, recency scoring
- [ ] **Similar repos engine** — Jaccard similarity on topics, category, star range
- [ ] **API rate limiting & caching** — Per-IP rate limiting, TTL cache, ETag support
- [ ] **OpenAPI spec** — Auto-generated docs at /api/docs
- [ ] Tests (target: 250+ total)

---

## Phase 3 — Web Frontend (Sessions 8–14)

- [ ] **Landing page** — Search bar, category grid, trending carousel, dark mode
- [ ] **Search results page** — Filterable sidebar, repo cards with Reepo Score badges
- [ ] **Repo detail page** — Score breakdown, README preview, similar repos, share button
- [ ] **Category browse pages** — /category/{slug}
- [ ] **Trending page** — Daily/weekly/monthly tabs
- [ ] **SEO infrastructure** — SSR/pre-rendering, OG tags, sitemap, structured data
- [ ] **OG share cards** — Dynamic 1200×630 PNG per repo
- [ ] **Responsive design** — Mobile-first
- [ ] Tests (target: 350+ total)

---

## Phase 4 — User Accounts & Collections (Sessions 15–20)

- [ ] **Auth system** — GitHub OAuth, JWT tokens
- [ ] **Collections** — Named, public/private saved lists of repos
- [ ] **Bookmarks** — Quick-save repos
- [ ] **User profile pages** — /u/{username}
- [ ] **Follow system** — Lightweight social layer
- [ ] **Notifications** — In-app + email digest
- [ ] **API keys** — User-generated keys with usage tracking
- [ ] **PostgreSQL migration**
- [ ] Tests (target: 500+ total)

---

## Phase 5 — Community & "Built With" Showcase (Sessions 21–26)

- [ ] **"Built With" submissions** — User-submitted projects using indexed repos
- [ ] **Upvotes** — Community curation
- [ ] **Comments** — Threaded, markdown, moderated
- [ ] **Weekly digest** — Auto-generated newsletter + blog post + RSS
- [ ] **Submit a repo** — User-suggested repo additions
- [ ] **Admin dashboard** — Moderation, user mgmt, index health
- [ ] **Blog / content pages** — SEO articles from index data
- [ ] Tests (target: 650+ total)

---

## Phase 6 — Monetization Infrastructure (Sessions 27–32)

- [ ] **Sponsored listings** — Labeled placements + sponsor analytics dashboard
- [ ] **Stripe integration** — Pro subscriptions ($9/mo or $79/yr)
- [ ] **Pro feature gates** — Unlimited collections, comparison tool, export, no ads
- [ ] **Comparison tool (Pro)** — Side-by-side repo comparison
- [ ] **Export (Pro)** — JSON/CSV/PDF export
- [ ] **Affiliate link system** — "Try hosted version" buttons with tracking
- [ ] **Newsletter sponsorship** — Subscriber mgmt, sponsor slots, booking system
- [ ] **Tiered API access** — Free/Pro/Enterprise with usage metering
- [ ] Tests (target: 800+ total)

---

## Phase 7 — Growth & Retention (Sessions 33–38)

- [ ] **Automated daily crawl** — Discover + re-analyze repos on schedule
- [ ] **GitHub App** — Real-time updates from repo owners
- [ ] **Embeddable badges** — SVG Reepo Score badges for READMEs
- [ ] **Chrome extension** — Reepo Score overlay on GitHub
- [ ] **Awesome List import** — Bulk-import from awesome-* repos
- [ ] **Personalized recommendations** — Collaborative filtering
- [ ] **Changelog tracking** — Per-repo timeline of notable changes
- [ ] **i18n** — Mandarin, Japanese, Spanish, Portuguese, Korean
- [ ] Tests (target: 950+ total)

---

## Phase 8 — Platform Maturity (Sessions 39+)

- [ ] **Performance optimization** — CDN, query optimization, <200ms p95 search
- [ ] **Analytics pipeline** — Page views, search queries, conversion funnel
- [ ] **Public stats page** — /stats with index growth over time
- [ ] **Contributor program** — Community moderators
- [ ] **Slack / Discord bot** — Search Reepo from chat
- [ ] **Reepo Score CI** — GitHub Action for PR checks
- [ ] **Open data export** — Monthly CC-BY CSV dump
- [ ] Tests (target: 1,000+ total)
