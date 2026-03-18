# Reepo.dev — Progress Summary

## What's Been Done

### User Accounts with Supabase Auth
- Replaced custom JWT auth with Supabase Auth (GitHub OAuth)
- Frontend: `AuthProvider` context, `useAuth` hook, `getAccessToken` helper
- Backend: Supabase JWT verification via `SUPABASE_JWT_SECRET` (HS256)
- User menu in header with avatar dropdown (Saved Repos, My Projects, Submit a Repo, Sign Out)
- Sign in with GitHub button when logged out

### Bookmarks (Save Repos)
- `POST/DELETE /api/bookmarks` — add/remove bookmarks
- `GET /api/bookmarks` — list user's bookmarked repos
- `GET /api/bookmarks/check?repo_ids=1,2,3` — batch check bookmark status
- Heart icon on repo detail page with optimistic toggle
- `/saved` page showing all bookmarked repos

### Repo Submissions
- `POST /api/submissions` — submit a GitHub URL for indexing
- `GET /api/submissions/mine` — user's past submissions with status
- `/submit` page with URL validation and submission history

### Projects (Built With)
- `POST /api/built-with` — submit a project
- `GET /api/built-with` — list projects (sort by upvotes or newest)
- `POST /api/built-with/{id}/upvote` — toggle upvote
- `GET /api/repos/{owner}/{name}/built-with` — projects using a specific repo
- `/projects` page with upvote/sort
- `/projects/new` submission form with repo search picker
- "Built with this" section on repo detail pages

### README About Sections (IN PROGRESS)
- Replaced regex-based excerpt extraction with LLM summarization via Ollama (gemma3:4b)
- `summarize_readme()` in `src/api/repos.py` sends README content to local Ollama and gets a paragraph-length summary
- New repo detail visits that have no cached excerpt will auto-generate one via the `/api/repos/{owner}/{name}/readme` endpoint
- Batch script at `scripts/batch_summarize.py` processes all repos in order of stars (descending)
- **300 of 16,471 repos completed** — top 300 by stars have LLM-generated summaries
- Script auto-resumes (skips repos with summaries > 150 chars)

## What's Left

### Resume README Batch (~16,171 repos remaining)

**Prerequisites on Mac Mini:**

1. Install Ollama desktop app from ollama.com (do NOT use `brew install ollama` — the homebrew build has Metal shader compilation bugs on macOS Tahoe)
2. Launch the Ollama app
3. Pull the model:
   ```bash
   ollama pull gemma3:4b
   ```
4. Verify it works:
   ```bash
   curl -s http://localhost:11434/api/generate -d '{"model":"gemma3:4b","prompt":"hello","stream":false}'
   ```

**Run the batch:**

```bash
cd /path/to/reepo-dev-platform
.venv/bin/python -u scripts/batch_summarize.py
```

- Automatically skips the 300 already-processed repos
- Processes remaining ~16,171 repos at ~0.19/s (~24 hours)
- Prints progress every 50 repos
- Commits each repo to DB individually (safe to kill and restart anytime)
- Checks GitHub rate limit every 500 repos (uses authenticated token, 5000 req/hr)

**If the venv doesn't exist on the Mac Mini:**
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### After Batch Completes

- Restart the backend server to clear the in-memory cache: kill the process and run `.venv/bin/uvicorn src.server:app --host 0.0.0.0 --port 8001`
- Verify a few repo About sections look good in the browser
- The frontend already displays the `readme_excerpt` field in the About section — no frontend changes needed

### Other Polish (Not Started)
- Polish SavedRepos, SubmitRepo, Projects, SubmitProject page designs
- Repo card bookmark icon on hover

## Running the App

**Backend:**
```bash
cd reepo-dev-platform
.venv/bin/uvicorn src.server:app --host 0.0.0.0 --port 8001
```

**Frontend:**
```bash
cd reepo-dev-platform/frontend
npm run dev
```

**Environment:** All secrets are in `.env.local` at project root. Vite reads it via `envDir` config. Backend reads it via `python-dotenv`.

## Key Files

| File | Purpose |
|------|---------|
| `src/api/repos.py` | Repo API routes + `summarize_readme()` (Ollama) |
| `scripts/batch_summarize.py` | Batch README summarization (auto-resumes) |
| `frontend/src/lib/auth.tsx` | Supabase auth context |
| `frontend/src/lib/api.ts` | All API client functions |
| `frontend/src/pages/RepoDetail.tsx` | Repo detail page (About, bookmarks, projects) |
| `frontend/src/components/layout.tsx` | Header with auth UI |
| `src/auth/jwt_auth.py` | Supabase JWT verification |
| `.env.local` | All secrets (Supabase, GitHub, Google OAuth) |
