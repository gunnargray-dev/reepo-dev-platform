import { useEffect, useState } from 'react';

interface AnalyticsSummary {
  total_views: number;
  unique_visitors: number;
  top_pages: { path: string; views: number }[];
  top_search_queries: { query: string; count: number; avg_results: number }[];
  top_repos_viewed: { path: string; views: number }[];
  conversion_funnel: { visits: number; searches: number; views: number; saves: number; signups: number; pro_upgrades: number };
  period_days: number;
}

export default function AdminAnalytics() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = 'Admin Analytics — Reepo.dev';
    setLoading(true);
    fetch(`/api/admin/analytics?days=${days}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) return <div className="max-w-5xl mx-auto px-4 py-12"><div className="animate-pulse h-96 bg-bg-card rounded" /></div>;
  if (!data) return <div className="max-w-5xl mx-auto px-4 py-20 text-center text-gray-400">Could not load analytics</div>;

  const funnel = data.conversion_funnel;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-white">Admin Analytics</h1>
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${days === d ? 'bg-accent text-white' : 'bg-bg-card text-gray-400 hover:text-white'}`}>
              {d}d
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-white">{data.total_views.toLocaleString()}</div>
          <div className="text-xs text-gray-400">Total Views</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-white">{data.unique_visitors.toLocaleString()}</div>
          <div className="text-xs text-gray-400">Unique Visitors</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-white">{funnel.searches.toLocaleString()}</div>
          <div className="text-xs text-gray-400">Searches</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-white">{funnel.pro_upgrades}</div>
          <div className="text-xs text-gray-400">Pro Upgrades</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">Top Pages</h3>
          <div className="space-y-2">
            {data.top_pages.slice(0, 10).map((p) => (
              <div key={p.path} className="flex items-center justify-between text-sm">
                <span className="text-gray-300 truncate">{p.path}</span>
                <span className="text-white font-mono ml-2">{p.views}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">Top Search Queries</h3>
          <div className="space-y-2">
            {data.top_search_queries.slice(0, 10).map((q) => (
              <div key={q.query} className="flex items-center justify-between text-sm">
                <span className="text-gray-300 truncate">{q.query}</span>
                <span className="text-white font-mono ml-2">{q.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Conversion Funnel</h3>
        <div className="flex items-end gap-4 h-32">
          {Object.entries(funnel).map(([step, value]) => {
            const maxVal = Math.max(...Object.values(funnel), 1);
            const height = Math.max(4, (value / maxVal) * 100);
            return (
              <div key={step} className="flex-1 flex flex-col items-center">
                <span className="text-xs text-white font-mono mb-1">{value}</span>
                <div className="w-full bg-accent/60 rounded-t" style={{ height: `${height}%` }} />
                <span className="text-xs text-gray-400 mt-1 truncate w-full text-center">{step}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
