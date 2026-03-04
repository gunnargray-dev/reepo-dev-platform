import { Link } from 'react-router-dom';
import type { Repo } from '../lib/api';
import { formatNumber, timeAgo, languageColor } from '../lib/utils';
import ScoreBadge from './ScoreBadge';

interface RepoCardProps {
  repo: Repo;
  showDelta?: number;
}

export default function RepoCard({ repo, showDelta }: RepoCardProps) {
  return (
    <Link to={`/repo/${repo.owner}/${repo.name}`} className="card block p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-accent font-semibold truncate">{repo.full_name}</h3>
            {repo.category_primary && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-bg-primary border border-border-subtle text-gray-400 whitespace-nowrap">{repo.category_primary}</span>
            )}
          </div>
          {repo.description && <p className="text-gray-400 text-sm mt-1.5 line-clamp-2">{repo.description}</p>}
          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500 flex-wrap">
            <span className="flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 16 16"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>
              {formatNumber(repo.stars)}
              {showDelta !== undefined && showDelta > 0 && <span className="text-score-green ml-1">+{formatNumber(showDelta)}</span>}
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 16 16"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75v-.878a2.25 2.25 0 111.5 0v.878a2.25 2.25 0 01-2.25 2.25h-1.5v2.128a2.251 2.251 0 11-1.5 0V8.5h-1.5A2.25 2.25 0 013.5 6.25v-.878a2.25 2.25 0 111.5 0zM5 3.25a.75.75 0 10-1.5 0 .75.75 0 001.5 0zm6.75.75a.75.75 0 10.75-.75.75.75 0 00-.75.75zM8 12.75a.75.75 0 10.75-.75.75.75 0 00-.75.75z"/></svg>
              {formatNumber(repo.forks)}
            </span>
            {repo.language && (
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: languageColor(repo.language) }} />
                {repo.language}
              </span>
            )}
            {repo.pushed_at && <span>Updated {timeAgo(repo.pushed_at)}</span>}
          </div>
        </div>
        <div className="flex-shrink-0"><ScoreBadge score={repo.reepo_score} /></div>
      </div>
    </Link>
  );
}
