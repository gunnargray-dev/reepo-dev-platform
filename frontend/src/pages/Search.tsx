import { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import RepoCard from '../components/RepoCard';
import Pagination from '../components/Pagination';
import type { Repo, CategoryInfo, StatsResponse } from '../lib/api';
import { searchRepos, getCategories, getStats } from '../lib/api';

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
    document.title = q ? `"${q}" — Search — Reepo.dev` : 'Search — Reepo.dev';
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{q ? `Results for "${q}"` : 'All Repos'}</h1>
          {!loading && <p className="text-sm text-gray-500 mt-1">{total} repos found</p>}
        </div>
        <button className="lg:hidden btn-secondary text-sm" onClick={() => setSidebarOpen(!sidebarOpen)}>Filters</button>
      </div>

      <div className="flex gap-8">
        <aside className={`${sidebarOpen ? 'block' : 'hidden'} lg:block w-full lg:w-56 flex-shrink-0`}>
          <div className="card p-4 space-y-6 sticky top-24">
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-3">Category</h3>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                <label className="flex items-center gap-2 text-sm text-gray-400 hover:text-white cursor-pointer">
                  <input type="radio" name="category" checked={!category} onChange={() => updateParam('category', '')} className="accent-accent" /> All
                </label>
                {categories.map((cat) => (
                  <label key={cat.slug} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white cursor-pointer">
                    <input type="radio" name="category" checked={category === cat.slug} onChange={() => updateParam('category', cat.slug)} className="accent-accent" />
                    {cat.name} <span className="text-gray-600 text-xs ml-auto">{cat.repo_count}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-3">Language</h3>
              <select value={language} onChange={(e) => updateParam('language', e.target.value)}
                className="w-full bg-bg-primary border border-border-subtle rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-accent">
                <option value="">All languages</option>
                {languages.map((lang) => <option key={lang} value={lang}>{lang}</option>)}
              </select>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-3">Min Score: <span className="font-mono text-accent">{minScore}</span></h3>
              <input type="range" min={0} max={100} step={5} value={minScore}
                onChange={(e) => updateParam('min_score', e.target.value === '0' ? '' : e.target.value)} className="w-full accent-accent" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-3">Sort by</h3>
              <select value={sort} onChange={(e) => updateParam('sort', e.target.value)}
                className="w-full bg-bg-primary border border-border-subtle rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-accent">
                {SORT_OPTIONS.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
              </select>
            </div>
          </div>
        </aside>

        <div className="flex-1 min-w-0">
          {loading ? (
            <div className="space-y-3">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="card p-5 h-24 animate-pulse" />)}</div>
          ) : repos.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold text-white mb-2">No repos found</h3>
              <p className="text-gray-500 mb-6">Try a different search term or adjust your filters.</p>
              <button onClick={() => navigate('/search')} className="btn-primary">Clear filters</button>
            </div>
          ) : (
            <>
              <div className="space-y-3">{repos.map((repo) => <RepoCard key={repo.id} repo={repo} />)}</div>
              <Pagination page={page} totalPages={totalPages} onPageChange={handlePageChange} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
