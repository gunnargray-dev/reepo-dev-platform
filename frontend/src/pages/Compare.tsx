import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { formatNumber, scoreColorVar } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScoreBadge } from '@/components/score-badge';

interface CompareRepo {
  id: number;
  full_name: string;
  stars: number;
  forks: number;
  language: string;
  license: string;
  reepo_score: number;
  score_breakdown: Record<string, number>;
  open_issues: number;
  pushed_at: string;
  category_primary: string;
}

export default function Compare() {
  const [params] = useSearchParams();
  const [repos, setRepos] = useState<CompareRepo[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const ids = params.get('ids') || '';

  useEffect(() => {
    document.title = 'Compare -- Reepo.dev';
    if (!ids) { setLoading(false); setError('Add ?ids=1,2,3 to compare repos'); return; }
    fetch(`/api/compare?repo_ids=${ids}&user_id=1`, { method: 'POST' })
      .then((r) => {
        if (r.status === 403) throw new Error('pro_required');
        if (!r.ok) throw new Error('failed');
        return r.json();
      })
      .then((data) => setRepos(data.repos))
      .catch((e) => setError(e.message === 'pro_required' ? 'pro_required' : 'Could not load comparison'))
      .finally(() => setLoading(false));
  }, [ids]);

  if (loading) return <div className="mx-auto max-w-4xl px-4 py-12"><Skeleton className="h-64" /></div>;

  if (error === 'pro_required') return (
    <div className="mx-auto max-w-3xl animate-fade-in px-4 py-20 text-center">
      <h1 className="text-xl font-semibold text-foreground mb-2">Pro feature</h1>
      <p className="mb-4 text-[14px] text-muted-foreground">The comparison tool requires a Pro subscription.</p>
      <Button asChild><Link to="/pricing">View pricing</Link></Button>
    </div>
  );

  if (error) return (
    <div className="mx-auto max-w-3xl px-4 py-20 text-center">
      <p className="text-[14px] text-muted-foreground">{error}</p>
    </div>
  );

  const rows = [
    { label: 'Score', render: (r: CompareRepo) => <ScoreBadge score={r.reepo_score} size="sm" /> },
    { label: 'Stars', render: (r: CompareRepo) => <span className="font-mono tabular-nums">{formatNumber(r.stars)}</span> },
    { label: 'Forks', render: (r: CompareRepo) => <span className="font-mono tabular-nums">{formatNumber(r.forks)}</span> },
    { label: 'Language', render: (r: CompareRepo) => r.language || '--' },
    { label: 'License', render: (r: CompareRepo) => r.license || '--' },
    { label: 'Issues', render: (r: CompareRepo) => <span className="font-mono tabular-nums">{formatNumber(r.open_issues)}</span> },
    { label: 'Last Push', render: (r: CompareRepo) => r.pushed_at ? new Date(r.pushed_at).toLocaleDateString() : '--' },
    { label: 'Category', render: (r: CompareRepo) => r.category_primary || '--' },
  ];

  const dimensions = ['maintenance_health', 'documentation_quality', 'community_activity', 'popularity', 'freshness', 'license_score'];
  const dimLabels: Record<string, string> = { maintenance_health: 'Maintenance', documentation_quality: 'Docs', community_activity: 'Community', popularity: 'Popularity', freshness: 'Freshness', license_score: 'License' };

  return (
    <div className="mx-auto max-w-4xl animate-fade-in px-4 py-8 sm:px-6">
      <h1 className="mb-6 text-xl font-semibold text-foreground">Compare</h1>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-28"></TableHead>
              {repos.map((r) => (
                <TableHead key={r.id}>
                  <Link to={`/repo/${r.full_name}`} className="hover:underline underline-offset-2">{r.full_name}</Link>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map(({ label, render }) => (
              <TableRow key={label}>
                <TableCell className="font-medium text-muted-foreground">{label}</TableCell>
                {repos.map((r) => <TableCell key={r.id}>{render(r)}</TableCell>)}
              </TableRow>
            ))}
            {dimensions.map((dim) => (
              <TableRow key={dim}>
                <TableCell className="font-medium text-muted-foreground">{dimLabels[dim] || dim}</TableCell>
                {repos.map((r) => {
                  const val = r.score_breakdown?.[dim];
                  return (
                    <TableCell key={r.id} className="font-mono tabular-nums" style={val ? { color: scoreColorVar(val) } : { color: 'var(--fg-subtle)' }}>
                      {val ?? '--'}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
