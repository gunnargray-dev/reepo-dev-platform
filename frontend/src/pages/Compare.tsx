import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { formatNumber, scoreColor } from '../lib/utils';
import ScoreBadge from '../components/ScoreBadge';

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
    document.title = 'Compare repos — Reepo.dev';
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

  if (loading) return <div className="max-w-6xl mx-auto px-4 py-12"><div className="animate-pulse h-64 bg-bg-card rounded" /></div>;

  if (error === 'pro_required') return (
    <div className="max-w-4xl mx-auto px-4 py-20 text-center">
      <h1 className="text-2xl font-bold text-white mb-4">Pro feature</h1>
      <p className="text-gray-400 mb-6">The comparison tool requires a Pro subscription.</p>
      <Link to="/pricing" className="btn-primary">View pricing</Link>
    </div>
  );

  if (error) return <div className="max-w-4xl mx-auto px-4 py-20 text-center"><p className="text-gray-400">{error}</p></div>;

  const rows = [
    { label: 'Score', render: (r: CompareRepo) => <ScoreBadge score={r.reepo_score} size="sm" /> },
    { label: 'Stars', render: (r: CompareRepo) => formatNumber(r.stars) },
    { label: 'Forks', render: (r: CompareRepo) => formatNumber(r.forks) },
    { label: 'Language', render: (r: CompareRepo) => r.language || '—' },
    { label: 'License', render: (r: CompareRepo) => r.license || '—' },
    { label: 'Issues', render: (r: CompareRepo) => formatNumber(r.open_issues) },
    { label: 'Last Push', render: (r: CompareRepo) => r.pushed_at ? new Date(r.pushed_at).toLocaleDateString() : '—' },
    { label: 'Category', render: (r: CompareRepo) => r.category_primary || '—' },
  ];

  const dimensions = ['maintenance_health', 'documentation_quality', 'community_activity', 'popularity', 'freshness', 'license_score'];
  const dimLabels: Record<string, string> = { maintenance_health: 'Maintenance', documentation_quality: 'Docs', community_activity: 'Community', popularity: 'Popularity', freshness: 'Freshness', license_score: 'License' };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Compare repos</h1>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-subtle">
              <th className="text-left text-gray-400 py-3 pr-4 w-32"></th>
              {repos.map((r) => (
                <th key={r.id} className="text-left text-white py-3 px-4 font-semibold">
                  <Link to={`/repo/${r.full_name}`} className="hover:text-accent">{r.full_name}</Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(({ label, render }) => (
              <tr key={label} className="border-b border-border-subtle/50">
                <td className="text-gray-400 py-3 pr-4 font-medium">{label}</td>
                {repos.map((r) => <td key={r.id} className="text-gray-300 py-3 px-4">{render(r)}</td>)}
              </tr>
            ))}
            {dimensions.map((dim) => (
              <tr key={dim} className="border-b border-border-subtle/50">
                <td className="text-gray-400 py-3 pr-4 font-medium">{dimLabels[dim] || dim}</td>
                {repos.map((r) => {
                  const val = r.score_breakdown?.[dim];
                  return <td key={r.id} className={`py-3 px-4 font-mono ${val ? scoreColor(val) : 'text-gray-500'}`}>{val ?? '—'}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
