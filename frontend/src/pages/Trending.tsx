import { useEffect, useState } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RepoCard } from '@/components/repo-card';
import type { TrendingRepo, Repo } from '@/lib/api';
import { getTrending, searchRepos } from '@/lib/api';

type Period = 'day' | 'week' | 'month';

export default function Trending() {
  const [period, setPeriod] = useState<Period>('week');
  const [trending, setTrending] = useState<TrendingRepo[]>([]);
  const [newRepos, setNewRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { document.title = 'Trending -- Reepo.dev'; }, []);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([getTrending(period, 20), searchRepos({ sort: 'updated_at', limit: 6 })]).then(([tr, nr]) => {
      if (tr.status === 'fulfilled') setTrending(tr.value);
      if (nr.status === 'fulfilled') setNewRepos(nr.value.repos);
      setLoading(false);
    });
  }, [period]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold text-foreground mb-6">Trending</h1>

      <Tabs value={period} onValueChange={(v) => setPeriod(v as Period)} className="mb-6">
        <TabsList>
          <TabsTrigger value="day">Day</TabsTrigger>
          <TabsTrigger value="week">Week</TabsTrigger>
          <TabsTrigger value="month">Month</TabsTrigger>
        </TabsList>
      </Tabs>

      {loading ? (
        <div className="space-y-2">{Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-[72px]" />)}</div>
      ) : trending.length === 0 ? (
        <div className="py-20 text-center">
          <h3 className="text-lg font-medium text-foreground mb-1">No trending data yet</h3>
          <p className="text-[14px] text-muted-foreground">Trending data appears after multiple crawl cycles.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {trending.map((repo, index) => (
            <div key={repo.id} className="flex items-center gap-3">
              <span className="w-6 shrink-0 text-right font-mono text-[13px] tabular-nums text-muted-foreground">{index + 1}</span>
              <div className="min-w-0 flex-1"><RepoCard repo={repo} showDelta={repo.star_delta} index={index} /></div>
            </div>
          ))}
        </div>
      )}

      {newRepos.length > 0 && (
        <div className="mt-14">
          <h2 className="mb-4 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Recently indexed</h2>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {newRepos.map((repo, i) => <RepoCard key={repo.id} repo={repo} index={i} />)}
          </div>
        </div>
      )}
    </div>
  );
}
