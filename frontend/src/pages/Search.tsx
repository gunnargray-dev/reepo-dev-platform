import { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Slider } from '@/components/ui/slider';
import { RepoCard } from '@/components/repo-card';
import { Pagination } from '@/components/pagination';
import type { Repo, CategoryInfo, StatsResponse } from '@/lib/api';
import { searchRepos, getCategories, getStats } from '@/lib/api';

const SORT_OPTIONS = [
  { value: 'stars', label: 'Stars' },
  { value: 'reepo_score', label: 'Score' },
  { value: 'updated_at', label: 'Newest' },
  { value: 'name', label: 'Name' },
];

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const q = searchParams.get('q') || '';
  const category = searchParams.get('category') || '';
  const language = searchParams.get('language') || '';
  const sort = searchParams.get('sort') || 'stars';
  const minScore = parseInt(searchParams.get('min_score') || '0', 10);
  const page = parseInt(searchParams.get('page') || '1', 10);

  const [repos, setRepos] = useState<Repo[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    document.title = q ? `"${q}" -- Search -- Reepo.dev` : 'Search -- Reepo.dev';
  }, [q]);

  useEffect(() => {
    Promise.allSettled([getCategories(), getStats()]).then(([catR, statsR]) => {
      if (catR.status === 'fulfilled') setCategories(catR.value);
      if (statsR.status === 'fulfilled') setLanguages(Object.keys((statsR.value as StatsResponse).by_language));
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    searchRepos({ q, category, language, min_score: minScore || undefined, sort, page, limit: 20 })
      .then((res) => { setRepos(res.repos); setTotal(res.total); setTotalPages(res.pages); })
      .catch(() => { setRepos([]); setTotal(0); setTotalPages(0); })
      .finally(() => setLoading(false));
  }, [q, category, language, sort, minScore, page]);

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

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">{q ? `Results for "${q}"` : 'All Repos'}</h1>
          {!loading && <p className="mt-0.5 font-mono text-[13px] tabular-nums text-muted-foreground">{total} repos</p>}
        </div>
        <Button variant="outline" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(!sidebarOpen)}>
          <SlidersHorizontal className="mr-2 h-3.5 w-3.5" />
          Filters
        </Button>
      </div>

      <div className="flex gap-8">
        <aside className={`${sidebarOpen ? 'block' : 'hidden'} w-full shrink-0 lg:block lg:w-48`}>
          <div className="sticky top-20 space-y-5">
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
              <div>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Sort</h3>
                <Select value={sort} onValueChange={(v) => updateParam('sort', v)}>
                  <SelectTrigger className="h-8 text-[13px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {SORT_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          {loading ? (
            <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-[72px]" />)}</div>
          ) : repos.length === 0 ? (
            <div className="py-20 text-center">
              <h3 className="text-lg font-medium text-foreground mb-1">No repos found</h3>
              <p className="mb-4 text-[14px] text-muted-foreground">Try a different search or adjust filters.</p>
              <Button onClick={() => navigate('/search')}>Clear filters</Button>
            </div>
          ) : (
            <>
              <div className="space-y-2">{repos.map((repo) => <RepoCard key={repo.id} repo={repo} />)}</div>
              <Pagination page={page} totalPages={totalPages} onPageChange={handlePageChange} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
