import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { formatNumber, languageColor, scoreColor, timeAgo } from '../lib/utils';
import ScoreBadge from '../components/ScoreBadge';
import type { Repo } from '../lib/api';

type CompareRepo = Repo;

export default function Compare() {
  const [searchParams] = useSearchParams();
  const [repos, setRepos] = useState<CompareRepo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ids = searchParams.get('ids') || '';

  useEffect(() => {
    document.title = 'Compare Repos — Reepo.dev';
    if (!ids) return;

    setLoading(true);
    setError(null);
    fetch(`/api/compare?repo_ids=${ids}&user_id=1`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 403 ? 'Pro subscription required' : 'Failed to load comparison');
        return r.json();
      })
      .then((data) => setRepos(data.repos))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ids]);

  const DIMENSIONS = ['maintenance_health', 'documentation_quality', 'community_activity', 'popularity', 'freshness', 'license_score'];
  const DIMENSION_LABELS: Record<string, string> = {
    maintenance_health: 'Maintenance', documentation_quality: 'Docs',
    community_activity: 'Community', popularity: 'Popularity',
    freshness: 'Freshness', license_score: 'License',
  };

  if (!ids) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <h1 className="text-2xl font-bold text-white mb-4">Compare Repos</h1>
        <p className="text-gray-400 mb-6">Select 2-5 repos to compare side-by-side.</p>
        <Link to="/search" className="btn-primary">Search repos</Link>
      </div>
    );
  }

  if (loading) return <div className="max-w-7xl mx-auto px-4 py-12"><div className="animate-pulse h-64 bg-bg-card rounded" /></div>;
  if (error) return (
    <div className="max-w-5xl mx-auto px-4 py-16 text-center">
      <h1 className="text-2xl font-bold text-white mb-4">Cannot Compare</h1>
      <p className="text-gray-400 mb-6">{error}</p>
      <Link to="/pricing" className="btn-primary">View pricing</Link>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Compare Repos</h1>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-subtle">
              <th className="text-left text-gray-400 font-medium py-3 px-4 w-32">Metric</th>
              {repos.map((r) => (
                <th key={r.id} className="text-left py-3 px-4">
                  <Link to={`/repo/${r.full_name}`} className="text-accent font-semibold hover:underline">{r.full_name}</Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            <tr>
              <td className="text-gray-400 py-3 px-4">Score</td>
              {repos.map((r) => <td key={r.id} className="py-3 px-4"><ScoreBadge score={r.reepo_score} /></td>)}
            </tr>
            <tr>
              <td className="text-gray-400 py-3 px-4">Stars</td>
              {repos.map((r) => <td key={r.id} className="py-3 px-4 text-white font-mono">{formatNumber(r.stars)}</td>)}
            </tr>
            <tr>
              <td className="text-gray-400 py-3 px-4">Forks</td>
              {repos.map((r) => <td key={r.id} className="py-3 px-4 text-white font-mono">{formatNumber(r.forks)}</td>)}
            </tr>
            <tr>
              <td className="text-gray-400 py-3 px-4">Language</td>
              {repos.map((r) => (
                <td key={r.id} className="py-3 px-4">
                  {r.language && <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: languageColor(r.language) }} />{r.language}</span>}
                </td>
              ))}
            </tr>
            <tr>
              <td className="text-gray-400 py-3 px-4">License</td>
              {repos.map((r) => <td key={r.id} className="py-3 px-4 text-gray-300">{r.license || '—'}</td>)}
            </tr>
            <tr>
              <td className="text-gray-400 py-3 px-4">Issues</td>
              {repos.map((r) => <td key={r.id} className="py-3 px-4 text-white font-mono">{formatNumber(r.open_issues)}</td>)}
            </tr>
            <tr>
              <td className="text-gray-400 py-3 px-4">Last Push</td>
              {repos.map((r) => <td key={r.id} className="py-3 px-4 text-gray-300">{r.pushed_at ? timeAgo(r.pushed_at) : '—'}</td>)}
            </tr>
            <tr>
              <td className="text-gray-400 py-3 px-4">Category</td>
              {repos.map((r) => <td key={r.id} className="py-3 px-4 text-gray-300">{r.category_primary || '—'}</td>)}
            </tr>
            {DIMENSIONS.map((dim) => (
              <tr key={dim}>
                <td className="text-gray-400 py-3 px-4">{DIMENSION_LABELS[dim]}</td>
                {repos.map((r) => {
                  const val = r.score_breakdown?.[dim as keyof typeof r.score_breakdown];
                  return (
                    <td key={r.id} className="py-3 px-4">
                      {val !== undefined ? <span className={`font-mono ${scoreColor(val)}`}>{val}</span> : '—'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
