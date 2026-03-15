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
  readme_excerpt: string | null;
  last_analyzed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  pushed_at: string | null;
  open_issues: number;
  has_wiki: boolean | number;
  homepage: string | null;
  indexed_at: string | null;
  use_cases: string[] | null;
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
