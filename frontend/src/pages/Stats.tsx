import { useEffect, useState } from 'react';

interface PublicStats {
  total_repos: number;
  repos_by_category: Record<string, number>;
  repos_by_language: Record<string, number>;
  avg_reepo_score: number;
  median_score: number;
  score_distribution: { excellent_80_plus: number; good_60_79: number; fair_40_59: number; poor_below_40: number };
  index_growth: { date: string; total_repos: number }[];
  top_repos_by_score: { full_name: string; reepo_score: number; stars: number; language: string }[];
  newest_repos: { full_name: string; description: string; stars: number; language: string }[];
}

function BarChart({ data, label }: { data: Record<string, number>; label: string }) {
  const entries = Object.entries(data);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-400 mb-3">{label}</h3>
      <div className="space-y-2">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-center gap-2 text-xs">
            <span className="text-gray-400 w-24 truncate text-right">{key}</span>
            <div className="flex-1 h-4 bg-bg-primary rounded overflow-hidden">
              <div className="h-full bg-accent/60 rounded" style={{ width: `${(value / max) * 100}%` }} />
            </div>
            <span className="text-gray-300 w-10 text-right">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Stats() {
  const [stats, setStats] = useState<PublicStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = 'Stats — Reepo.dev';
    fetch('/api/public-stats')
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="max-w-5xl mx-auto px-4 py-12"><div className="animate-pulse h-96 bg-bg-card rounded" /></div>;
  if (!stats) return <div className="max-w-5xl mx-auto px-4 py-20 text-center text-gray-400">Could not load stats</div>;

  const dist = stats.score_distribution;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-white mb-2">Reepo Index Stats</h1>
      <p className="text-gray-400 mb-8">Open data about our AI repo index</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-white">{stats.total_repos.toLocaleString()}</div>
          <div className="text-xs text-gray-400">Total Repos</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-white">{stats.avg_reepo_score}</div>
          <div className="text-xs text-gray-400">Avg Score</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-white">{stats.median_score}</div>
          <div className="text-xs text-gray-400">Median Score</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-white">{Object.keys(stats.repos_by_category).length}</div>
          <div className="text-xs text-gray-400">Categories</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
        <div className="card p-6">
          <BarChart data={stats.repos_by_category} label="Repos by Category" />
        </div>
        <div className="card p-6">
          <BarChart data={stats.repos_by_language} label="Top Languages" />
        </div>
      </div>

      <div className="card p-6 mb-10">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Score Distribution</h3>
        <div className="grid grid-cols-4 gap-4 text-center">
          <div><div className="text-xl font-bold text-score-green">{dist.excellent_80_plus}</div><div className="text-xs text-gray-400">80+</div></div>
          <div><div className="text-xl font-bold text-score-yellow">{dist.good_60_79}</div><div className="text-xs text-gray-400">60-79</div></div>
          <div><div className="text-xl font-bold text-orange-400">{dist.fair_40_59}</div><div className="text-xs text-gray-400">40-59</div></div>
          <div><div className="text-xl font-bold text-score-red">{dist.poor_below_40}</div><div className="text-xs text-gray-400">&lt;40</div></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">Top Repos by Score</h3>
          <div className="space-y-2">
            {stats.top_repos_by_score.map((r) => (
              <div key={r.full_name} className="flex items-center justify-between text-sm">
                <a href={`/repo/${r.full_name}`} className="text-white hover:text-accent truncate">{r.full_name}</a>
                <span className="text-score-green font-mono ml-2">{r.reepo_score}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">Recently Indexed</h3>
          <div className="space-y-2">
            {stats.newest_repos.map((r) => (
              <div key={r.full_name} className="flex items-center justify-between text-sm">
                <a href={`/repo/${r.full_name}`} className="text-white hover:text-accent truncate">{r.full_name}</a>
                <span className="text-gray-400 ml-2">{r.language || '—'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-10 text-center">
        <a href="/api/open-data/latest.csv" className="btn-secondary text-sm inline-flex items-center gap-1">
          Download Open Data (CSV)
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
        </a>
      </div>
    </div>
  );
}
