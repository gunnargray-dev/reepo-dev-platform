import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { CategoryCard } from '@/components/category-card';
import { RepoCard } from '@/components/repo-card';
import type { CategoryInfo, StatsResponse, Repo } from '@/lib/api';
import { getCategories, getStats, searchRepos, getTrending } from '@/lib/api';
import { formatNumber } from '@/lib/utils';

interface TrendingRepo extends Repo {
  star_delta?: number;
}

const QUICK_SEARCHES = [
  'RAG frameworks',
  'image generation',
  'coding agents',
  'voice cloning',
  'fine-tuning',
  'vector databases',
  'LLM inference',
  'computer vision',
];

export default function Home() {
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [categoryRepos, setCategoryRepos] = useState<Record<string, { full_name: string; owner: string }[]>>({});
  const [trending, setTrending] = useState<TrendingRepo[]>([]);

  useEffect(() => {
    document.title = 'Reepo.dev -- Discover Open Source AI';
    Promise.allSettled([getCategories(), getStats(), getTrending('week', 8)]).then(([catR, statsR, trendR]) => {
      if (catR.status === 'fulfilled') setCategories(catR.value);
      if (statsR.status === 'fulfilled') setStats(statsR.value);
      if (trendR.status === 'fulfilled' && trendR.value.length > 0) {
        setTrending(trendR.value);
      } else {
        // Fallback: top scored repos
        searchRepos({ sort: 'reepo_score', limit: 8 }).then((res) => {
          setTrending(res.repos);
        }).catch(() => {});
      }
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
    <div className="relative">
      {/* Glow background — spans full page */}
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden" aria-hidden="true">
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[800px] rounded-full bg-[radial-gradient(ellipse_at_center,var(--glow-center)_0%,var(--glow-mid)_40%,transparent_70%)] opacity-60 blur-[20px]" />
          <div className="absolute left-1/4 top-1/3 h-[300px] w-[300px] rounded-full bg-[radial-gradient(circle,var(--glow-accent)_0%,transparent_70%)] opacity-40 blur-[40px] animate-[glow-drift_8s_ease-in-out_infinite]" />
          <div className="absolute right-1/4 top-2/3 h-[250px] w-[250px] rounded-full bg-[radial-gradient(circle,var(--glow-accent2)_0%,transparent_70%)] opacity-30 blur-[40px] animate-[glow-drift_10s_ease-in-out_infinite_reverse]" />
          <div className="absolute inset-0" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\' opacity=\'0.04\'/%3E%3C/svg%3E")', backgroundRepeat: 'repeat', backgroundSize: '256px 256px' }} />
      </div>

      {/* Hero */}
      <section className="relative px-4 py-20 sm:py-28">
        <div className="mx-auto max-w-2xl text-center animate-slide-up">
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

          {/* Quick search chips */}
          <div className="mt-4 flex flex-wrap items-center justify-center gap-1.5">
            {QUICK_SEARCHES.map((q) => (
              <Link
                key={q}
                to={`/search?q=${encodeURIComponent(q)}`}
                className="rounded-full border border-border/60 px-3 py-1 text-[12px] text-muted-foreground transition-colors hover:border-border hover:text-foreground hover:bg-accent/10"
              >
                {q}
              </Link>
            ))}
          </div>

          <div className="mx-auto mt-6 h-px w-24 bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>
      </section>

      {/* Trending */}
      {trending.length > 0 && (
        <section className="mx-auto max-w-5xl px-4 pb-14 sm:px-6 animate-fade-in" style={{ animationDelay: '0.05s' }}>
          <h2 className="mb-4 flex items-center gap-2 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">
            <TrendingUp className="h-3.5 w-3.5" />
            {trending[0]?.star_delta ? 'Trending this week' : 'Top scored'}
          </h2>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {trending.map((repo) => (
              <RepoCard key={repo.id} repo={repo} showDelta={repo.star_delta} />
            ))}
          </div>
        </section>
      )}

      {/* Categories */}
      {categories.length > 0 && (
        <section className="mx-auto max-w-5xl px-4 pb-14 sm:px-6 animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <h2 className="mb-4 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Categories</h2>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
            {categories.map((cat) => <CategoryCard key={cat.slug} category={cat} topRepos={categoryRepos[cat.slug]} />)}
          </div>
        </section>
      )}
    </div>
  );
}
