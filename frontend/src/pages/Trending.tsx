import { useEffect, useState } from 'react';
import RepoCard from '../components/RepoCard';
import type { TrendingRepo, Repo } from '../lib/api';
import { getTrending, searchRepos } from '../lib/api';

type Period = 'day' | 'week' | 'month';
const PERIODS: { value: Period; label: string }[] = [
  { value: 'day', label: 'Day' },
  { value: 'week', label: 'Week' },
  { value: 'month', label: 'Month' },
];

export default function Trending() {
  const [period, setPeriod] = useState<Period>('week');
  const [trending, setTrending] = useState<TrendingRepo[]>([]);
  const [newRepos, setNewRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { document.title = 'Trending — Reepo.dev'; }, []);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([getTrending(period, 20), searchRepos({ sort: 'updated_at', limit: 6 })]).then(([tr, nr]) => {
      if (tr.status === 'fulfilled') setTrending(tr.value);
      if (nr.status === 'fulfilled') setNewRepos(nr.value.repos);
      setLoading(false);
    });
  }, [period]);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-white mb-6">Trending</h1>

      <div className="flex items-center gap-1 mb-8 bg-bg-card border border-border-subtle rounded-lg p-1 w-fit">
        {PERIODS.map(({ value, label }) => (
          <button key={value} onClick={() => setPeriod(value)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${period === value ? 'bg-accent text-white' : 'text-gray-400 hover:text-white'}`}>{label}</button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">{Array.from({ length: 10 }).map((_, i) => <div key={i} className="card p-5 h-24 animate-pulse" />)}</div>
      ) : trending.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-4xl mb-4">📈</div>
          <h3 className="text-xl font-semibold text-white mb-2">No trending data yet</h3>
          <p className="text-gray-500">Trending data appears after multiple crawl cycles.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {trending.map((repo, index) => (
            <div key={repo.id} className="flex items-center gap-4">
              <span className="text-lg font-mono text-gray-500 w-8 text-right flex-shrink-0">{index + 1}</span>
              <div className="flex-1 min-w-0"><RepoCard repo={repo} showDelta={repo.star_delta} /></div>
            </div>
          ))}
        </div>
      )}

      {newRepos.length > 0 && (
        <div className="mt-16">
          <h2 className="text-xl font-semibold text-white mb-4">Recently indexed</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {newRepos.map((repo) => <RepoCard key={repo.id} repo={repo} />)}
          </div>
        </div>
      )}
    </div>
  );
}
