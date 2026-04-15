import { useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { Search as SearchIcon, SlidersHorizontal, Sparkles, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { RepoCard } from '@/components/repo-card';
import { Pagination } from '@/components/pagination';
import { AIStackResults, type BuildIntent, type StackPick } from '@/components/AIStack';
import type { Repo, CategoryInfo, StatsResponse } from '@/lib/api';
import { searchRepos, getCategories, getStats } from '@/lib/api';

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'stars', label: 'Stars' },
  { value: 'score', label: 'Score' },
  { value: 'newest', label: 'Newest' },
  { value: 'name', label: 'Name' },
];

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const q = searchParams.get('q') || '';
  const category = searchParams.get('category') || '';
  const language = searchParams.get('language') || '';
  const sort = searchParams.get('sort') || (q ? 'relevance' : 'stars');
  const minScore = parseInt(searchParams.get('min_score') || '0', 10);
  const page = parseInt(searchParams.get('page') || '1', 10);
  // Routing mode: auto | keyword | ai. Default auto when q present so backend can route.
  const modeParam = (searchParams.get('mode') || (q ? 'auto' : 'keyword')) as 'auto' | 'keyword' | 'ai';
  // Filters/sort/pagination only make sense for keyword. Force keyword if any filter active.
  const filtersActive = Boolean(category || language || minScore > 0 || page > 1);
  const effectiveModeParam: 'auto' | 'keyword' | 'ai' = filtersActive ? 'keyword' : modeParam;

  const [repos, setRepos] = useState<Repo[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [inputValue, setInputValue] = useState(q);
  // AI-mode state.
  const [resolvedMode, setResolvedMode] = useState<'keyword' | 'ai'>('keyword');
  const [aiIntent, setAiIntent] = useState<BuildIntent | null>(null);
  const [aiPicks, setAiPicks] = useState<StackPick[]>([]);
  const [aiDegraded, setAiDegraded] = useState(false);

  useEffect(() => {
    document.title = q ? `"${q}" -- Search -- Reepo.dev` : 'Search -- Reepo.dev';
  }, [q]);

  useEffect(() => {
    setInputValue(q);
  }, [q]);

  useEffect(() => {
    Promise.allSettled([getCategories(), getStats()]).then(([catR, statsR]) => {
      if (catR.status === 'fulfilled') setCategories(catR.value);
      if (statsR.status === 'fulfilled') setLanguages(Object.keys((statsR.value as StatsResponse).by_language));
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    let cancelled = false;

    // AI/auto routing path: hit /api/search?mode=auto|ai directly so we can read the
    // discriminated response shape. Falls back to keyword render if backend says so.
    if (q && (effectiveModeParam === 'auto' || effectiveModeParam === 'ai')) {
      const url = new URL('/api/search', window.location.origin);
      url.searchParams.set('q', q);
      url.searchParams.set('mode', effectiveModeParam);
      fetch(url.toString())
        .then((r) => r.json())
        .then((data) => {
          if (cancelled) return;
          if (data?.mode === 'ai') {
            setResolvedMode('ai');
            setAiIntent((data.intent ?? null) as BuildIntent | null);
            setAiPicks((data.picks ?? []) as StackPick[]);
            setAiDegraded(Boolean(data.degraded));
            setRepos([]);
            setTotal((data.picks ?? []).length);
            setTotalPages(0);
          } else {
            // keyword shape from search_routes: { results, total, page, pages, mode }
            setResolvedMode('keyword');
            setAiIntent(null);
            setAiPicks([]);
            setAiDegraded(false);
            setRepos((data?.results ?? []) as Repo[]);
            setTotal(data?.total ?? 0);
            setTotalPages(data?.pages ?? 0);
          }
        })
        .catch(() => {
          if (cancelled) return;
          setResolvedMode('keyword');
          setRepos([]);
          setTotal(0);
          setTotalPages(0);
        })
        .finally(() => { if (!cancelled) setLoading(false); });
      return () => { cancelled = true; };
    }

    // Pure keyword path (filters active, explicit mode=keyword, or empty q).
    setResolvedMode('keyword');
    setAiIntent(null);
    setAiPicks([]);
    setAiDegraded(false);
    searchRepos({ q, category, language, min_score: minScore || undefined, sort, page, limit: 20 })
      .then((res) => { if (cancelled) return; setRepos(res.repos); setTotal(res.total); setTotalPages(res.pages); })
      .catch(() => { if (cancelled) return; setRepos([]); setTotal(0); setTotalPages(0); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [q, category, language, sort, minScore, page, effectiveModeParam]);

  const updateParam = useCallback((key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value); else next.delete(key);
    next.delete('page');
    setSearchParams(next);
  }, [searchParams, setSearchParams]);

  const handlePageChange = useCallback((p: number) => {
    const next = new URLSearchParams(searchParams);
    next.set('page', String(p));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [searchParams, setSearchParams]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const next = new URLSearchParams(searchParams);
    if (inputValue.trim()) {
      next.set('q', inputValue.trim());
      if (!next.has('sort') || next.get('sort') === 'stars') next.set('sort', 'relevance');
    } else {
      next.delete('q');
      if (next.get('sort') === 'relevance') next.delete('sort');
    }
    next.delete('page');
    setSearchParams(next);
  };

  const clearSearch = () => {
    setInputValue('');
    const next = new URLSearchParams(searchParams);
    next.delete('q');
    next.delete('page');
    if (next.get('sort') === 'relevance') next.delete('sort');
    setSearchParams(next);
    inputRef.current?.focus();
  };

  const activeFilters = [category, language, minScore > 0 ? `${minScore}+` : ''].filter(Boolean).length;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      {/* Search bar */}
      <form onSubmit={handleSearch} className="mb-6 animate-slide-up">
        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Search repos..."
            className="h-11 w-full rounded-lg border border-border bg-background pl-10 pr-10 text-[14px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/30"
          />
          {inputValue && (
            <button type="button" onClick={clearSearch} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </form>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">{q ? `Results for "${q}"` : 'All Repos'}</h1>
          {!loading && resolvedMode === 'keyword' && (
            <p className="mt-0.5 font-mono text-[13px] tabular-nums text-muted-foreground">{total} repos</p>
          )}
          {!loading && resolvedMode === 'ai' && (
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <Badge variant="secondary" className="gap-1 text-[11px]">
                <Sparkles className="h-3 w-3" />
                AI-recommended stack
              </Badge>
              <Link
                to={`/search?q=${encodeURIComponent(q)}&mode=keyword`}
                className="text-[12px] text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
              >
                View as keyword search →
              </Link>
            </div>
          )}
        </div>
        {resolvedMode === 'keyword' && (
          <Button variant="outline" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <SlidersHorizontal className="mr-2 h-3.5 w-3.5" />
            Filters{activeFilters > 0 && ` (${activeFilters})`}
          </Button>
        )}
      </div>

      {resolvedMode === 'ai' && !loading && (
        <div className="min-w-0">
          <AIStackResults intent={aiIntent} picks={aiPicks} degraded={aiDegraded} />
        </div>
      )}

      {resolvedMode === 'keyword' && (
      <div className="flex gap-8">
        <aside className={`${sidebarOpen ? 'block' : 'hidden'} w-full shrink-0 lg:block lg:w-48`}>
          <div className="sticky top-20 space-y-5">
              <div>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Sort</h3>
                <Select value={sort} onValueChange={(v) => updateParam('sort', v)}>
                  <SelectTrigger className="h-8 text-[13px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {SORT_OPTIONS.filter((opt) => opt.value !== 'relevance' || q).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Category</h3>
                <div className="space-y-0.5">
                  <label className="flex cursor-pointer items-center gap-2 py-0.5 text-[13px] text-muted-foreground hover:text-foreground">
                    <input type="radio" name="category" checked={!category} onChange={() => updateParam('category', '')} className="accent-foreground" /> All
                  </label>
                  {categories.map((cat) => (
                    <label key={cat.slug} className="flex cursor-pointer items-center gap-2 py-0.5 text-[13px] text-muted-foreground hover:text-foreground">
                      <input type="radio" name="category" checked={category === cat.slug} onChange={() => updateParam('category', cat.slug)} className="accent-foreground" />
                      <span className="truncate">{cat.name}</span>
                      <span className="ml-auto font-mono text-[11px] text-muted-foreground">{cat.repo_count}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Language</h3>
                <Select value={language || 'all'} onValueChange={(v) => updateParam('language', v === 'all' ? '' : v)}>
                  <SelectTrigger className="h-8 text-[13px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    {languages.map((lang) => <SelectItem key={lang} value={lang}>{lang}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  Min score <span className="font-mono text-foreground">{minScore}</span>
                </h3>
                <Slider
                  value={[minScore]}
                  onValueChange={([v]) => updateParam('min_score', v === 0 ? '' : String(v))}
                  min={0} max={100} step={5}
                />
              </div>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          {loading ? null : repos.length === 0 ? (
            <div className="py-20 text-center">
              <h3 className="text-lg font-medium text-foreground mb-1">No repos found</h3>
              <p className="mb-4 text-[14px] text-muted-foreground">
                {q ? `No results for "${q}". Try different keywords or adjust filters.` : 'Try a different search or adjust filters.'}
              </p>
              <Button onClick={() => navigate('/search')}>Clear filters</Button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {repos.map((repo) => (
                  <RepoCard key={repo.id} repo={repo} snippet={(repo as any).snippet} />
                ))}
              </div>
              <Pagination page={page} totalPages={totalPages} onPageChange={handlePageChange} />
            </>
          )}
        </div>
      </div>
      )}
    </div>
  );
}
