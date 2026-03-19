export interface Repo {
  id: number;
  github_id: number;
  owner: string;
  name: string;
  full_name: string;
  description: string | null;
  url: string;
  stars: number;
  forks: number;
  language: string | null;
  license: string | null;
  topics: string[];
  category_primary: string | null;
  categories_secondary: string[];
  reepo_score: number | null;
  score_breakdown: ScoreBreakdown | null;
  use_cases: string[] | null;
  score_percentile?: number;
  readme_excerpt: string | null;
  last_analyzed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  pushed_at: string | null;
  open_issues: number;
  has_wiki: boolean | number;
  homepage: string | null;
  indexed_at: string | null;
  star_delta?: number;
}

export type TrendingRepo = Repo;

export interface ScoreBreakdown {
  maintenance_health: number;
  documentation_quality: number;
  community_activity: number;
  popularity: number;
  freshness: number;
  license_score: number;
}

export interface CategoryInfo {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  repo_count: number;
}

export interface StatsResponse {
  total_repos: number;
  by_category: Record<string, number>;
  by_language: Record<string, number>;
  score_stats: {
    avg_score: number;
    min_score: number;
    max_score: number;
    distribution: {
      excellent_80_plus: number;
      good_60_79: number;
      fair_40_59: number;
      poor_below_40: number;
    };
  };
}

export interface SearchParams {
  q?: string;
  category?: string;
  language?: string;
  min_score?: number;
  sort?: string;
  page?: number;
  limit?: number;
}

export interface SearchResponse {
  repos: Repo[];
  total: number;
  page: number;
  pages: number;
}

const BASE = '/api';

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== '' && String(v) !== '0') {
        url.searchParams.set(k, String(v));
      }
    }
  }
  return url.toString();
}

export async function searchRepos(params: SearchParams): Promise<SearchResponse> {
  const data = await fetchJson<{ results: Repo[]; total: number; page: number; pages: number }>(buildUrl('/search', {
    q: params.q,
    category: params.category,
    language: params.language,
    min_score: params.min_score,
    sort: params.sort,
    page: params.page,
    per_page: params.limit,
  }));
  return { repos: data.results, total: data.total, page: data.page, pages: data.pages };
}

export async function getRepo(owner: string, name: string): Promise<Repo> {
  return fetchJson<Repo>(buildUrl(`/repos/${owner}/${name}`));
}

export async function getCategories(): Promise<CategoryInfo[]> {
  const data = await fetchJson<{ categories: CategoryInfo[] }>(buildUrl('/categories'));
  return data.categories;
}

export interface TagInfo {
  tag: string;
  count: number;
}

export async function getCategoryTags(slug: string): Promise<TagInfo[]> {
  const data = await fetchJson<{ tags: TagInfo[] }>(buildUrl(`/categories/${slug}/tags`));
  return data.tags;
}

export async function getTrending(period: string = 'week', limit: number = 20): Promise<TrendingRepo[]> {
  const data = await fetchJson<{ results: TrendingRepo[] }>(buildUrl('/trending', { period, limit }));
  return data.results;
}

export async function getStats(): Promise<StatsResponse> {
  return fetchJson<StatsResponse>(buildUrl('/stats'));
}

export async function getFeatured(): Promise<Repo[]> {
  const data = await fetchJson<{ repos: Repo[] }>(buildUrl('/featured'));
  return data.repos;
}

export async function getRepoReadme(owner: string, name: string): Promise<string | null> {
  const data = await fetchJson<{ readme: string | null }>(buildUrl(`/repos/${owner}/${name}/readme`));
  return data.readme;
}

export async function getSimilarRepos(owner: string, name: string): Promise<Repo[]> {
  const data = await fetchJson<{ results: Repo[] }>(buildUrl(`/repos/${owner}/${name}/similar`));
  return data.results;
}

export interface ScoreHistoryEntry { score: number; recorded_at: string; }

export async function getScoreHistory(owner: string, name: string): Promise<ScoreHistoryEntry[]> {
  const data = await fetchJson<{ history: ScoreHistoryEntry[] }>(buildUrl(`/repos/${owner}/${name}/history`));
  return data.history;
}

import { getAccessToken } from './auth'

async function fetchJsonAuth<T>(url: string, options: RequestInit = {}): Promise<T> {
  const token = await getAccessToken()
  const headers: Record<string, string> = {
    ...options.headers as Record<string, string>,
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const res = await fetch(url, { ...options, headers })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `API error: ${res.status}`)
  }
  return res.json()
}

// Bookmarks
export async function getBookmarks(): Promise<Repo[]> {
  const data = await fetchJsonAuth<{ bookmarks: any[] }>(`${BASE}/bookmarks`)
  return data.bookmarks
}

export async function addBookmark(repoId: number): Promise<void> {
  await fetchJsonAuth(`${BASE}/bookmarks/${repoId}`, { method: 'POST' })
}

export async function removeBookmark(repoId: number): Promise<void> {
  await fetchJsonAuth(`${BASE}/bookmarks/${repoId}`, { method: 'DELETE' })
}

export async function checkBookmarks(repoIds: number[]): Promise<number[]> {
  if (repoIds.length === 0) return []
  const data = await fetchJsonAuth<{ bookmarked: number[] }>(
    buildUrl('/bookmarks/check', { repo_ids: repoIds.join(',') })
  )
  return data.bookmarked
}

// Submissions
export async function submitRepo(githubUrl: string): Promise<{ id: number; status: string }> {
  return fetchJsonAuth(`${BASE}/submissions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ github_url: githubUrl }),
  })
}

export async function getMySubmissions(): Promise<any[]> {
  return fetchJsonAuth(`${BASE}/submissions/mine`)
}

// Projects (Built With)
export interface Project {
  id: number
  title: string
  description: string
  url: string
  screenshot_url: string | null
  status: string
  upvote_count: number
  created_at: string
  repo_ids?: number[]
}

export async function getProjects(sort: string = 'upvotes', limit: number = 20, offset: number = 0): Promise<Project[]> {
  return fetchJson<Project[]>(buildUrl('/built-with', { sort, limit, offset }))
}

export async function getProject(id: number): Promise<Project> {
  return fetchJson<Project>(`${BASE}/built-with/${id}`)
}

export async function submitProject(data: {
  title: string
  description: string
  url: string
  repo_ids: number[]
  screenshot_url?: string
}): Promise<{ id: number; status: string }> {
  return fetchJsonAuth(`${BASE}/built-with`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function upvoteProject(id: number): Promise<{ upvoted: boolean }> {
  return fetchJsonAuth(`${BASE}/built-with/${id}/upvote`, { method: 'POST' })
}

export async function getRepoProjects(owner: string, name: string): Promise<Project[]> {
  return fetchJson<Project[]>(`${BASE}/repos/${owner}/${name}/built-with`)
}

export interface ScoreResult {
  repo: {
    owner: string;
    name: string;
    full_name: string;
    description: string;
    url: string;
    stars: number;
    forks: number;
    language: string | null;
    license: string | null;
    category: string;
  };
  reepo_score: number;
  score_breakdown: ScoreBreakdown;
}

export async function scoreRepo(url: string): Promise<ScoreResult> {
  const res = await fetch(`${BASE}/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error: ${res.status}`);
  }
  return res.json();
}
