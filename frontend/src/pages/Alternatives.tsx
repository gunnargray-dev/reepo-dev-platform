import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Star, AlertCircle } from 'lucide-react';
import type { Repo } from '@/lib/api';
import { getRepo, getSimilarRepos } from '@/lib/api';
import { formatNumber, timeAgo, scoreColorVar, languageColor } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScoreBadge } from '@/components/score-badge';

export default function Alternatives() {
  const { owner, name } = useParams<{ owner: string; name: string }>();
  const [repo, setRepo] = useState<Repo | null>(null);
  const [alternatives, setAlternatives] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!owner || !name) return;
    setLoading(true);
    document.title = `Alternatives to ${owner}/${name} -- Reepo.dev`;
    Promise.allSettled([getRepo(owner, name), getSimilarRepos(owner, name)]).then(([rr, sr]) => {
      if (rr.status === 'fulfilled') setRepo(rr.value);
      if (sr.status === 'fulfilled') setAlternatives(sr.value);
      setLoading(false);
    });
  }, [owner, name]);

  if (loading) return null;

  if (!repo) return (
    <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6">
      <AlertCircle className="mx-auto h-10 w-10 text-muted-foreground" />
      <h1 className="mt-4 text-xl font-semibold text-foreground">Repo not found</h1>
      <p className="mt-1 text-[14px] text-muted-foreground">{owner}/{name} is not in our index.</p>
      <Button asChild className="mt-4">
        <Link to="/search">Search repos</Link>
      </Button>
    </div>
  );

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold text-foreground">
        Alternatives to{' '}
        <Link to={`/repo/${repo.owner}/${repo.name}`} className="underline underline-offset-2 hover:text-muted-foreground">
          {repo.full_name}
        </Link>
      </h1>

      <Card className="mt-4">
        <CardContent className="flex items-center gap-4 p-4">
          <img src={`https://github.com/${repo.owner}.png?size=32`} alt="" className="h-8 w-8 rounded-md" />
          <div className="min-w-0 flex-1">
            <p className="text-[14px] font-medium text-foreground truncate">{repo.full_name}</p>
            {repo.description && <p className="text-[13px] text-muted-foreground line-clamp-1">{repo.description}</p>}
          </div>
          <div className="flex items-center gap-3 text-[12px] text-muted-foreground">
            <span className="flex items-center gap-1"><Star className="h-3 w-3" />{formatNumber(repo.stars)}</span>
            {repo.language && (
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: languageColor(repo.language) }} />
                {repo.language}
              </span>
            )}
            {repo.license && <Badge variant="secondary" className="text-[10px]">{repo.license}</Badge>}
          </div>
          <ScoreBadge score={repo.reepo_score} />
        </CardContent>
      </Card>

      {alternatives.length === 0 ? (
        <div className="py-16 text-center">
          <p className="text-[14px] text-muted-foreground">No alternatives found yet.</p>
        </div>
      ) : (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-border text-left text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                <th className="pb-2 pr-4">Repo</th>
                <th className="pb-2 pr-4 text-right">Score</th>
                <th className="pb-2 pr-4 text-right">Stars</th>
                <th className="pb-2 pr-4 hidden sm:table-cell">Language</th>
                <th className="pb-2 pr-4 hidden md:table-cell">License</th>
                <th className="pb-2 hidden md:table-cell text-right">Last Push</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {alternatives.map((alt) => (
                <tr key={alt.id} className="group">
                  <td className="py-2.5 pr-4">
                    <Link to={`/repo/${alt.owner}/${alt.name}`} className="font-medium text-foreground hover:underline underline-offset-2">
                      {alt.full_name}
                    </Link>
                    {alt.description && (
                      <p className="mt-0.5 text-[12px] text-muted-foreground line-clamp-1">{alt.description}</p>
                    )}
                  </td>
                  <td className="py-2.5 pr-4 text-right">
                    {alt.reepo_score !== null ? (
                      <span className="font-mono tabular-nums font-medium" style={{ color: scoreColorVar(alt.reepo_score) }}>
                        {alt.reepo_score}
                      </span>
                    ) : <span className="text-muted-foreground">--</span>}
                  </td>
                  <td className="py-2.5 pr-4 text-right font-mono tabular-nums text-muted-foreground">
                    {formatNumber(alt.stars)}
                  </td>
                  <td className="py-2.5 pr-4 hidden sm:table-cell">
                    {alt.language && (
                      <span className="flex items-center gap-1.5 text-muted-foreground">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: languageColor(alt.language) }} />
                        {alt.language}
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 pr-4 hidden md:table-cell text-muted-foreground">
                    {alt.license || '\u2014'}
                  </td>
                  <td className="py-2.5 hidden md:table-cell text-right text-muted-foreground">
                    {alt.pushed_at ? timeAgo(alt.pushed_at) : '\u2014'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
