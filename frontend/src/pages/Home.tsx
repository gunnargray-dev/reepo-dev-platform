import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Sparkles, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { CategoryCard } from '@/components/category-card';
import { RepoCard } from '@/components/repo-card';
import { NetworkBg } from '@/components/network-bg';
import type { CategoryInfo, StatsResponse, Repo } from '@/lib/api';
import { getCategories, getStats, searchRepos, getTrending, getFeatured } from '@/lib/api';
import { formatNumber } from '@/lib/utils';
import { useAuth } from '@/lib/auth';

interface TrendingRepo extends Repo {
  star_delta?: number;
}

const QUICK_SEARCHES = [
  'RAG frameworks',
  'coding agents',
  'UI component libraries',
  'design systems',
  'image generation',
  'icon libraries',
  'vector databases',
  'CSS frameworks',
];

export default function Home() {
  const { user, loading: authLoading, signIn } = useAuth();
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [categoryRepos, setCategoryRepos] = useState<Record<string, { full_name: string; owner: string }[]>>({});
  const [trending, setTrending] = useState<TrendingRepo[]>([]);
  const [featured, setFeatured] = useState<Repo[]>([]);

  useEffect(() => {
    document.title = 'Reepo.dev -- Discover Open Source';
    Promise.allSettled([getCategories(), getStats(), getTrending('week', 8), getFeatured()]).then(([catR, statsR, trendR, featR]) => {
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
      if (featR.status === 'fulfilled') setFeatured(featR.value);
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
      {/* Interactive network background */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-0 h-[520px] overflow-hidden sm:h-[600px]" aria-hidden="true">
          <NetworkBg />
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[800px] rounded-full bg-[radial-gradient(ellipse_at_center,var(--glow-center)_0%,var(--glow-mid)_40%,transparent_70%)] opacity-60 blur-[20px]" />
          <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-b from-transparent to-background" />
      </div>

      {/* Hero */}
      <section className="relative z-10 px-4 py-20 sm:py-28">
        <div className="mx-auto max-w-2xl text-center animate-slide-up">
          <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-5xl leading-[1.1]">
Discover, save, and share the best open source repos
          </h1>
          <p className="mt-3 text-[15px] text-muted-foreground">
            Reepo scores open source projects on maintenance, docs, community, and more.
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
        <section className="relative z-10 mx-auto max-w-5xl px-4 pb-14 sm:px-6 animate-fade-in" style={{ animationDelay: '0.05s' }}>
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

      {/* Featured */}
      {featured.length > 0 && (
        <section className="relative z-10 mx-auto max-w-5xl px-4 pb-14 sm:px-6 animate-fade-in" style={{ animationDelay: '0.08s' }}>
          <h2 className="mb-4 flex items-center gap-2 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5" />
            Featured
          </h2>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {featured.map((repo) => (
              <RepoCard key={repo.id} repo={repo} />
            ))}
          </div>
        </section>
      )}

      {/* Categories */}
      {categories.length > 0 && (
        <section className="relative z-10 mx-auto max-w-5xl px-4 pb-14 sm:px-6 animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <h2 className="mb-4 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Categories</h2>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
            {categories.map((cat) => <CategoryCard key={cat.slug} category={cat} topRepos={categoryRepos[cat.slug]} />)}
          </div>
        </section>
      )}

      {/* CTAs */}
      <section className="relative z-10 mx-auto max-w-5xl px-4 py-20 sm:px-6">
        <div className="mx-auto h-px w-24 bg-gradient-to-r from-transparent via-border to-transparent mb-16" />
        <div className={`grid gap-6 ${!authLoading && !user ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 max-w-md mx-auto'}`}>
          {/* Score CTA */}
          <div className="rounded-xl border border-border/60 p-8 text-center">
            <h2 className="text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
              Get your Reepo Score
            </h2>
            <p className="mt-3 text-[14px] text-muted-foreground">
              Paste any GitHub repo and instantly see how it scores on maintenance, docs, community, and more.
            </p>
            <Button asChild size="lg" variant="outline" className="mt-6">
              <Link to="/score">Score a repo</Link>
            </Button>
          </div>

          {/* Sign up CTA */}
          {!authLoading && !user && (
            <div className="rounded-xl border border-border/60 p-8 text-center">
              <h2 className="text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
                Save and share repos
              </h2>
              <p className="mt-3 text-[14px] text-muted-foreground">
                Bookmark repos, build collections, and showcase projects you've built with the community.
              </p>
              <Button onClick={signIn} size="lg" className="mt-6">
                Sign up with GitHub
              </Button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
