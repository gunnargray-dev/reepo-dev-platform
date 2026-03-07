import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { StatCard } from '@/components/stat-card';
import { scoreColorVar } from '@/lib/utils';

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

function HorizontalBar({ data, label }: { data: Record<string, number>; label: string }) {
  const entries = Object.entries(data);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <div>
      <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{label}</h3>
      <div className="space-y-1.5">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-center gap-2 text-[13px]">
            <span className="w-20 truncate text-right text-muted-foreground">{key}</span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-foreground/20 transition-all duration-300" style={{ width: `${(value / max) * 100}%` }} />
            </div>
            <span className="w-8 text-right font-mono tabular-nums text-foreground">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DistributionViz({ dist }: { dist: PublicStats['score_distribution'] }) {
  const segments = [
    { label: '80+', value: dist.excellent_80_plus, color: 'var(--score-high)' },
    { label: '60-79', value: dist.good_60_79, color: 'var(--score-mid)' },
    { label: '40-59', value: dist.fair_40_59, color: 'var(--score-mid)' },
    { label: '<40', value: dist.poor_below_40, color: 'var(--score-low)' },
  ];
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;

  return (
    <div>
      <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Score distribution</h3>
      <div className="flex h-2 gap-px overflow-hidden rounded-full">
        {segments.map((s) => (
          <div key={s.label} className="transition-all duration-300" style={{ width: `${(s.value / total) * 100}%`, backgroundColor: s.color }} />
        ))}
      </div>
      <div className="mt-2 flex justify-between">
        {segments.map((s) => (
          <div key={s.label} className="text-center">
            <div className="font-mono text-[15px] font-semibold tabular-nums" style={{ color: s.color }}>{s.value}</div>
            <div className="text-[11px] text-muted-foreground">{s.label}</div>
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
    document.title = 'Stats -- Reepo.dev';
    fetch('/api/public-stats')
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return null;
  if (!stats) return <div className="mx-auto max-w-3xl px-4 py-20 text-center text-muted-foreground">Could not load stats</div>;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold text-foreground">Index Stats</h1>
      <p className="mt-1 text-[14px] text-muted-foreground">Open data about the Reepo AI repo index</p>

      <div className="mt-6 grid grid-cols-2 gap-2 md:grid-cols-4">
        <StatCard label="Total Repos" value={stats.total_repos.toLocaleString()} />
        <StatCard label="Avg Score" value={String(stats.avg_reepo_score)} />
        <StatCard label="Median" value={String(stats.median_score)} />
        <StatCard label="Categories" value={String(Object.keys(stats.repos_by_category).length)} />
      </div>

      <Card className="mt-6">
        <CardContent className="p-5">
          <DistributionViz dist={stats.score_distribution} />
        </CardContent>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card><CardContent className="p-5"><HorizontalBar data={stats.repos_by_category} label="By category" /></CardContent></Card>
        <Card><CardContent className="p-5"><HorizontalBar data={stats.repos_by_language} label="Top languages" /></CardContent></Card>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Top by score</h3>
            <div className="space-y-1.5">
              {stats.top_repos_by_score.map((r) => (
                <div key={r.full_name} className="flex items-center justify-between text-[13px]">
                  <Link to={`/repo/${r.full_name}`} className="truncate text-foreground hover:underline underline-offset-2">{r.full_name}</Link>
                  <span className="ml-2 font-mono tabular-nums" style={{ color: scoreColorVar(r.reepo_score) }}>{r.reepo_score}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Recently indexed</h3>
            <div className="space-y-1.5">
              {stats.newest_repos.map((r) => (
                <div key={r.full_name} className="flex items-center justify-between text-[13px]">
                  <Link to={`/repo/${r.full_name}`} className="truncate text-foreground hover:underline underline-offset-2">{r.full_name}</Link>
                  <span className="ml-2 text-muted-foreground">{r.language || '--'}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 text-center">
        <Button variant="outline" size="sm" asChild>
          <a href="/api/open-data/latest.csv">
            <Download className="mr-1.5 h-3 w-3" />
            Download CSV
          </a>
        </Button>
      </div>
    </div>
  );
}
