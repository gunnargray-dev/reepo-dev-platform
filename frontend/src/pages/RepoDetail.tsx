import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Star, GitFork, ExternalLink, Copy, Check, AlertCircle } from 'lucide-react';
import type { Repo } from '@/lib/api';
import { getRepo, getSimilarRepos, getRepoReadme, getScoreHistory } from '@/lib/api';
import type { ScoreHistoryEntry } from '@/lib/api';
import { formatNumber, timeAgo, languageColor, scoreColorVar } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { RepoCard } from '@/components/repo-card';
import { DimensionCell } from '@/components/dimension-bar';
import { ScoreSparkline } from '@/components/score-sparkline';
import { getUseCases } from '@/lib/use-cases';

const DIMENSIONS: Record<string, string> = {
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
  const [readme, setReadme] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [history, setHistory] = useState<ScoreHistoryEntry[]>([]);

  useEffect(() => {
    if (!owner || !name) return;
    setLoading(true);
    setReadme(null);
    document.title = `${owner}/${name} -- Reepo.dev`;
    Promise.allSettled([getRepo(owner, name), getSimilarRepos(owner, name)]).then(([rr, sr]) => {
      if (rr.status === 'fulfilled') setRepo(rr.value);
      if (sr.status === 'fulfilled') setSimilar(sr.value);
      setLoading(false);
    });
    getRepoReadme(owner, name).then(setReadme).catch(() => {});
    getScoreHistory(owner, name).then(setHistory).catch(() => {});
  }, [owner, name]);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const useCases = useMemo(
    () => (repo ? getUseCases(repo.topics || [], repo.category_primary) : []),
    [repo],
  );

  if (loading) return null;

  if (!repo) return (
    <div className="mx-auto max-w-5xl px-4 py-20 text-center sm:px-6">
      <AlertCircle className="mx-auto h-10 w-10 text-muted-foreground" />
      <h1 className="mt-4 text-xl font-semibold text-foreground">Repo not found</h1>
      <p className="mt-1 text-[14px] text-muted-foreground">{owner}/{name} is not in our index.</p>
      <Button asChild className="mt-4">
        <Link to="/search">Search repos</Link>
      </Button>
    </div>
  );

  const scoreColor = scoreColorVar(repo.reepo_score);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div className="flex gap-8">
        {/* Main content */}
        <div className="min-w-0 flex-1">
          {/* Header */}
          <div className="flex items-start gap-3">
            <img
              src={`https://github.com/${repo.owner}.png?size=40`}
              alt=""
              className="h-10 w-10 rounded-lg"
            />
            <div className="min-w-0">
              <h1 className="text-xl font-semibold text-foreground truncate">{repo.full_name}</h1>
              {repo.description && (
                <p className="mt-1 text-[15px] leading-relaxed text-muted-foreground">{repo.description}</p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="mt-4 flex items-center gap-2">
            <Button asChild size="sm">
              <a href={repo.url} target="_blank" rel="noopener noreferrer">
                GitHub <ExternalLink className="ml-1.5 h-3 w-3" />
              </a>
            </Button>
            {repo.homepage && (
              <Button asChild variant="outline" size="sm">
                <a href={repo.homepage} target="_blank" rel="noopener noreferrer">Website</a>
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={handleShare}>
              {copied ? <><Check className="mr-1.5 h-3 w-3" />Copied</> : <><Copy className="mr-1.5 h-3 w-3" />Share</>}
            </Button>
          </div>

          {/* Meta */}
          <div className="mt-5 flex flex-wrap items-center gap-4 text-[13px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <Star className="h-3.5 w-3.5" />
              <strong className="font-medium text-foreground">{formatNumber(repo.stars)}</strong>
            </span>
            <span className="flex items-center gap-1">
              <GitFork className="h-3.5 w-3.5" />
              <strong className="font-medium text-foreground">{formatNumber(repo.forks)}</strong>
            </span>
            <span>{formatNumber(repo.open_issues)} issues</span>
            {repo.license && <span>{repo.license}</span>}
            {repo.language && (
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: languageColor(repo.language) }} />
                {repo.language}
              </span>
            )}
            {repo.created_at && <span>{timeAgo(repo.created_at)}</span>}
          </div>

          {/* Summary */}
          {readme && (
            <div className="mt-6">
              <h2 className="mb-2 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">About</h2>
              <p className="text-[14px] leading-relaxed text-foreground/80">{readme}</p>
            </div>
          )}

          {/* Use Cases */}
          {useCases.length > 0 && (
            <div className="mt-8 pt-6 border-t border-border/50">
              <h2 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Use cases</h2>
              <ul className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
                {useCases.map((c) => (
                  <li key={c} className="flex items-start gap-2 text-[14px] text-foreground/80">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/40" />
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Topics */}
          {repo.topics && repo.topics.length > 0 && (
            <div className="mt-8 pt-6 border-t border-border/50">
              <h2 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Topics</h2>
              <div className="flex flex-wrap gap-1.5">
                {repo.topics.map((topic) => (
                  <Badge key={topic} variant="secondary" asChild>
                    <Link to={`/search?q=${encodeURIComponent(topic)}`}>{topic}</Link>
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar — Score */}
        <aside className="hidden w-56 shrink-0 lg:block">
          <div className="sticky top-20 rounded-lg border border-border/50 bg-card p-4 border-l-2" style={{ borderLeftColor: scoreColor }}>
            <div className="flex items-center gap-2">
              <div
                className="text-4xl font-bold font-mono tabular-nums"
                style={{ color: scoreColor }}
              >
                {repo.reepo_score ?? '--'}
              </div>
              <div className="text-[12px] text-muted-foreground leading-tight">
                <div>Reepo</div>
                <div>Score</div>
              </div>
            </div>
            {repo.score_breakdown && (
              <div className="mt-3 divide-y divide-border">
                {Object.entries(repo.score_breakdown).map(([key, value]) => (
                  <DimensionCell key={key} label={DIMENSIONS[key] || key} value={value} compact />
                ))}
              </div>
            )}
            <ScoreSparkline data={history} />
          </div>
        </aside>
      </div>

      {/* Mobile score — below content on small screens */}
      <div className="mt-8 lg:hidden">
        <Card className="border-l-2" style={{ borderLeftColor: scoreColor }}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <div
                className="text-4xl font-bold font-mono tabular-nums"
                style={{ color: scoreColor }}
              >
                {repo.reepo_score ?? '--'}
              </div>
              <div className="text-[12px] text-muted-foreground leading-tight">
                <div>Reepo</div>
                <div>Score</div>
              </div>
            </div>
            {repo.score_breakdown && (
              <div className="mt-3 grid grid-cols-3 gap-2">
                {Object.entries(repo.score_breakdown).map(([key, value]) => (
                  <DimensionCell key={key} label={DIMENSIONS[key] || key} value={value} />
                ))}
              </div>
            )}
            <ScoreSparkline data={history} />
          </CardContent>
        </Card>
      </div>

      {/* Similar */}
      {similar.length > 0 && (
        <div className="mt-12 pt-8 border-t border-border/50">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Similar repos</h2>
            <Link
              to={`/alternatives/${repo.owner}/${repo.name}`}
              className="text-[13px] text-muted-foreground transition-colors hover:text-foreground"
            >
              View all alternatives &rarr;
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {similar.slice(0, 4).map((r) => <RepoCard key={r.id} repo={r} />)}
          </div>
        </div>
      )}
    </div>
  );
}
