import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatCard } from '@/components/stat-card';

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
    document.title = 'Analytics -- Reepo.dev';
    setLoading(true);
    fetch(`/api/admin/analytics?days=${days}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) return null;
  if (!data) return <div className="mx-auto max-w-3xl px-4 py-20 text-center text-muted-foreground">Could not load analytics</div>;

  const funnel = data.conversion_funnel;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">Analytics</h1>
        <Tabs value={String(days)} onValueChange={(v) => setDays(Number(v))}>
          <TabsList>
            <TabsTrigger value="7">7d</TabsTrigger>
            <TabsTrigger value="30">30d</TabsTrigger>
            <TabsTrigger value="90">90d</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-2 md:grid-cols-4">
        <StatCard label="Views" value={data.total_views.toLocaleString()} />
        <StatCard label="Visitors" value={data.unique_visitors.toLocaleString()} />
        <StatCard label="Searches" value={funnel.searches.toLocaleString()} />
        <StatCard label="Pro" value={String(funnel.pro_upgrades)} />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Top pages</h3>
            <div className="space-y-1.5">
              {data.top_pages.slice(0, 10).map((p) => (
                <div key={p.path} className="flex items-center justify-between text-[13px]">
                  <span className="truncate text-muted-foreground">{p.path}</span>
                  <span className="ml-2 font-mono tabular-nums text-foreground">{p.views}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Top queries</h3>
            <div className="space-y-1.5">
              {data.top_search_queries.slice(0, 10).map((q) => (
                <div key={q.query} className="flex items-center justify-between text-[13px]">
                  <span className="truncate text-muted-foreground">{q.query}</span>
                  <span className="ml-2 font-mono tabular-nums text-foreground">{q.count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-5">
          <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Funnel</h3>
          <div className="flex h-28 items-end gap-3">
            {Object.entries(funnel).map(([step, value]) => {
              const maxVal = Math.max(...Object.values(funnel), 1);
              const height = Math.max(4, (value / maxVal) * 100);
              return (
                <div key={step} className="flex flex-1 flex-col items-center">
                  <span className="mb-1 font-mono text-[11px] tabular-nums text-foreground">{value}</span>
                  <div className="w-full rounded-sm bg-foreground/15" style={{ height: `${height}%` }} />
                  <span className="mt-1.5 w-full truncate text-center text-[11px] text-muted-foreground">{step}</span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
