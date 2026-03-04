import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { Repo } from '../lib/api';
import { getRepo, getSimilarRepos } from '../lib/api';
import { formatNumber, timeAgo, languageColor, scoreColor } from '../lib/utils';
import ScoreBadge from '../components/ScoreBadge';
import RepoCard from '../components/RepoCard';

const DIMENSION_LABELS: Record<string, string> = {
  maintenance_health: 'Maintenance',
  documentation_quality: 'Documentation',
  community_activity: 'Community',
  popularity: 'Popularity',
  freshness: 'Freshness',
  license_score: 'License',
};

export default function RepoDetail() {
  const { owner, name } = useParams<{ owner: string; name: string }>();
  const [repo, setRepo] = useState<Repo | null>(null);
  const [similar, setSimilar] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!owner || !name) return;
    setLoading(true);
    document.title = `${owner}/${name} — Reepo.dev`;
    Promise.allSettled([getRepo(owner, name), getSimilarRepos(owner, name)]).then(([rr, sr]) => {
      if (rr.status === 'fulfilled') setRepo(rr.value);
      if (sr.status === 'fulfilled') setSimilar(sr.value);
      setLoading(false);
    });
  }, [owner, name]);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });
  };

  if (loading) return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="animate-pulse space-y-6"><div className="h-8 bg-bg-card rounded w-1/2" /><div className="h-4 bg-bg-card rounded w-3/4" /><div className="h-64 bg-bg-card rounded" /></div>
    </div>
  );

  if (!repo) return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
      <h1 className="text-2xl font-bold text-white mb-4">Repo not found</h1>
      <p className="text-gray-500 mb-6">{owner}/{name} is not in our index.</p>
      <Link to="/search" className="btn-primary">Search repos</Link>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3">
            <img src={`https://github.com/${repo.owner}.png?size=48`} alt={repo.owner} className="w-10 h-10 rounded-lg" />
            <h1 className="text-2xl sm:text-3xl font-bold text-white">{repo.full_name}</h1>
          </div>
          {repo.description && <p className="text-gray-400 mt-3 text-lg max-w-3xl">{repo.description}</p>}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleShare} className="btn-secondary text-sm">{copied ? 'Copied!' : 'Share'}</button>
          <a href={repo.url} target="_blank" rel="noopener noreferrer" className="btn-primary text-sm inline-flex items-center gap-1">
            GitHub
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
          </a>
          {repo.homepage && <a href={repo.homepage} target="_blank" rel="noopener noreferrer" className="btn-secondary text-sm">Website</a>}
        </div>
      </div>

      <div className="flex items-center gap-5 mt-6 flex-wrap text-sm text-gray-400">
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 16 16"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>
          <strong className="text-white">{formatNumber(repo.stars)}</strong> stars
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 16 16"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75v-.878a2.25 2.25 0 111.5 0v.878a2.25 2.25 0 01-2.25 2.25h-1.5v2.128a2.251 2.251 0 11-1.5 0V8.5h-1.5A2.25 2.25 0 013.5 6.25v-.878a2.25 2.25 0 111.5 0zM5 3.25a.75.75 0 10-1.5 0 .75.75 0 001.5 0zm6.75.75a.75.75 0 10.75-.75.75.75 0 00-.75.75zM8 12.75a.75.75 0 10.75-.75.75.75 0 00-.75.75z"/></svg>
          <strong className="text-white">{formatNumber(repo.forks)}</strong> forks
        </span>
        <span>{formatNumber(repo.open_issues)} issues</span>
        {repo.license && <span>{repo.license}</span>}
        {repo.language && (
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: languageColor(repo.language) }} />
            {repo.language}
          </span>
        )}
        {repo.created_at && <span>Created {timeAgo(repo.created_at)}</span>}
      </div>

      <div className="card p-6 mt-8">
        <div className="flex items-center gap-4 mb-6">
          <h2 className="text-lg font-semibold text-white">Reepo Score</h2>
          <ScoreBadge score={repo.reepo_score} size="md" />
        </div>
        {repo.score_breakdown && (
          <div className="space-y-3">
            {Object.entries(repo.score_breakdown).map(([key, value]) => (
              <div key={key} className="flex items-center gap-3">
                <span className="text-sm text-gray-400 w-28 flex-shrink-0">{DIMENSION_LABELS[key] || key}</span>
                <div className="flex-1 h-2.5 bg-bg-primary rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-500 ${value >= 80 ? 'bg-score-green' : value >= 50 ? 'bg-score-yellow' : 'bg-score-red'}`} style={{ width: `${value}%` }} />
                </div>
                <span className={`text-sm font-mono w-8 text-right ${scoreColor(value)}`}>{value}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {repo.topics && repo.topics.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold text-white mb-3">Topics</h2>
          <div className="flex flex-wrap gap-2">
            {repo.topics.map((topic) => (
              <Link key={topic} to={`/search?q=${encodeURIComponent(topic)}`}
                className="text-xs px-3 py-1.5 rounded-full bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 transition-colors">{topic}</Link>
            ))}
          </div>
        </div>
      )}

      {similar.length > 0 && (
        <div className="mt-12">
          <h2 className="text-lg font-semibold text-white mb-4">Similar repos</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {similar.map((r) => <RepoCard key={r.id} repo={r} />)}
          </div>
        </div>
      )}
    </div>
  );
}
