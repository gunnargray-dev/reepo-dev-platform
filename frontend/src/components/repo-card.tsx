import { Link } from 'react-router-dom';
import { Star, GitFork, Heart } from 'lucide-react';
import type { Repo } from '@/lib/api';
import { formatNumber, timeAgo, languageColor } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { ScoreBadge } from '@/components/score-badge';

interface RepoCardProps {
  repo: Repo;
  showDelta?: number;
  snippet?: string;
  isBookmarked?: boolean;
  onToggleBookmark?: (repoId: number) => void;
}

function renderSnippet(snippet: string) {
  // Backend uses « » as highlight markers
  const parts = snippet.split(/(«[^»]*»)/g);
  return parts.map((part, i) => {
    if (part.startsWith('«') && part.endsWith('»')) {
      return <mark key={i} className="bg-transparent font-medium text-foreground">{part.slice(1, -1)}</mark>;
    }
    return part;
  });
}

export function RepoCard({ repo, showDelta, snippet, isBookmarked, onToggleBookmark }: RepoCardProps) {
  return (
    <Link
      to={`/repo/${repo.owner}/${repo.name}`}
      className="group relative flex items-start justify-between gap-3 rounded-lg border border-border/60 bg-card px-4 py-3.5 transition-all duration-150 hover:border-border/80 hover:bg-accent/5 hover:shadow-[0_2px_8px_-2px_rgba(0,0,0,0.08)] dark:hover:shadow-[0_2px_8px_-2px_rgba(0,0,0,0.3)] hover:-translate-y-px"
    >
      <img
        src={`https://github.com/${repo.owner}.png?size=64`}
        alt=""
        className="h-8 w-8 shrink-0 rounded-md mt-0.5"
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-[15px] font-medium text-foreground group-hover:underline underline-offset-2 truncate">
            {repo.full_name}
          </h3>
          {repo.category_primary && (
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
              {repo.category_primary}
            </Badge>
          )}
        </div>
        {snippet ? (
          <p className="mt-1.5 text-[13px] text-muted-foreground line-clamp-2">{renderSnippet(snippet)}</p>
        ) : repo.description ? (
          <p className="mt-1.5 text-[13px] text-muted-foreground line-clamp-1">{repo.description}</p>
        ) : null}
        <div className="mt-2.5 flex items-center gap-3.5 text-[12px] text-muted-foreground opacity-60 group-hover:opacity-100 transition-opacity">
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
      {onToggleBookmark && (
        <button
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); onToggleBookmark(repo.id); }}
          className="absolute top-2 right-2 rounded-md p-1 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:text-foreground"
          aria-label={isBookmarked ? 'Remove bookmark' : 'Bookmark'}
        >
          <Heart className={`h-3.5 w-3.5 ${isBookmarked ? 'fill-current text-foreground' : ''}`} />
        </button>
      )}
    </Link>
  );
}
