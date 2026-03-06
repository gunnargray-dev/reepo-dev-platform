import { Link } from 'react-router-dom';
import { Star, GitFork } from 'lucide-react';
import type { Repo } from '@/lib/api';
import { formatNumber, timeAgo, languageColor } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { ScoreBadge } from '@/components/score-badge';

interface RepoCardProps {
  repo: Repo;
  showDelta?: number;
}

export function RepoCard({ repo, showDelta }: RepoCardProps) {
  return (
    <Link
      to={`/repo/${repo.owner}/${repo.name}`}
      className="group flex items-start justify-between gap-3 rounded-lg border border-border bg-card px-4 py-3.5 transition-colors hover:border-border/80 hover:bg-accent/5"
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-[14px] font-medium text-foreground group-hover:underline underline-offset-2 truncate">
            {repo.full_name}
          </h3>
          {repo.category_primary && (
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
              {repo.category_primary}
            </Badge>
          )}
        </div>
        {repo.description && (
          <p className="mt-1 text-[13px] text-muted-foreground line-clamp-1">{repo.description}</p>
        )}
        <div className="mt-2 flex items-center gap-3.5 text-[12px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Star className="h-3 w-3" />
            {formatNumber(repo.stars)}
            {showDelta !== undefined && showDelta > 0 && (
              <span style={{ color: 'var(--score-high)' }}>+{formatNumber(showDelta)}</span>
            )}
          </span>
          <span className="flex items-center gap-1">
            <GitFork className="h-3 w-3" />
            {formatNumber(repo.forks)}
          </span>
          {repo.language && (
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: languageColor(repo.language) }} />
              {repo.language}
            </span>
          )}
          {repo.pushed_at && <span>{timeAgo(repo.pushed_at)}</span>}
        </div>
      </div>
      <div className="shrink-0">
        <ScoreBadge score={repo.reepo_score} />
      </div>
    </Link>
  );
}
