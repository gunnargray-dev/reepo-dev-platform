import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { CategoryCard } from '@/components/category-card';
import { RepoCard } from '@/components/repo-card';
import type { CategoryInfo, Repo, StatsResponse } from '@/lib/api';
import { getCategories, getTrending, getStats, searchRepos } from '@/lib/api';
import { formatNumber } from '@/lib/utils';

export default function Home() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [trending, setTrending] = useState<Repo[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [categoryRepos, setCategoryRepos] = useState<Record<string, { full_name: string; owner: string }[]>>({});

  useEffect(() => {
    document.title = 'Reepo.dev -- Discover Open Source AI';
    Promise.allSettled([getCategories(), getTrending('week', 6), getStats()]).then(([catR, trendR, statsR]) => {
      if (catR.status === 'fulfilled') setCategories(catR.value);
      if (trendR.status === 'fulfilled') setTrending(trendR.value);
      if (statsR.status === 'fulfilled') setStats(statsR.value);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (categories.length === 0) return;
    const fetchTopRepos = async () => {
      const entries: Record<string, { full_name: string; owner: string }[]> = {};
      await Promise.allSettled(
        categories.map(async (cat) => {
          const res = await searchRepos({ category: cat.slug, sort: 'reepo_score', limit: 3 });
          entries[cat.slug] = res.repos.map((r) => ({ full_name: r.full_name, owner: r.owner }));
        })
      );
      setCategoryRepos(entries);
    };
    fetchTopRepos();
  }, [categories]);

  return (
    <div className="animate-fade-in">
      <section className="px-4 py-20 sm:py-28">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-5xl leading-[1.1]">
            Discover the best AI repos
          </h1>
          <p className="mt-3 text-[15px] text-muted-foreground">
            Reepo scores {stats ? `${formatNumber(stats.total_repos)}+` : ''} open source AI projects on maintenance, docs, community, and more.
          </p>
          <div className="mt-8 flex justify-center">
            <Button
              variant="outline"
              className="h-11 w-full max-w-md justify-start rounded-lg border-border text-muted-foreground"
              onClick={() => {
                document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
              }}
            >
              <Search className="mr-2 h-4 w-4" />
              <span>Search repos...</span>
              <kbd className="pointer-events-none ml-auto hidden h-5 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:flex">
                <span className="text-xs">⌘</span>K
              </kbd>
            </Button>
          </div>
          {stats && (
            <div className="mt-6 flex items-center justify-center gap-3 text-[13px] text-muted-foreground">
              <span className="font-mono tabular-nums">{formatNumber(stats.total_repos)}</span>
              <span>repos</span>
              <span className="text-border">/</span>
              <span className="font-mono tabular-nums">{Object.keys(stats.by_category).length}</span>
              <span>categories</span>
              <span className="text-border">/</span>
              <span>avg score <span className="font-mono tabular-nums">{stats.score_stats.avg_score}</span></span>
            </div>
          )}
          <div className="mx-auto mt-6 h-px w-24 bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 pb-14 sm:px-6">
        <h2 className="mb-4 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Categories</h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
          {categories.map((cat) => <CategoryCard key={cat.slug} category={cat} topRepos={categoryRepos[cat.slug]} />)}
        </div>
      </section>

      {trending.length > 0 && (
        <section className="mx-auto max-w-5xl px-4 pb-14 sm:px-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Trending this week</h2>
            <button
              onClick={() => navigate('/trending')}
              className="text-[13px] text-muted-foreground transition-colors hover:text-foreground"
            >
              View all &rarr;
            </button>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {trending.map((repo) => <RepoCard key={repo.id} repo={repo} />)}
          </div>
        </section>
      )}
    </div>
  );
}
