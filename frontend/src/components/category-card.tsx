import { Link } from 'react-router-dom';
import type { CategoryInfo } from '@/lib/api';
import { scoreColorVar } from '@/lib/utils';

interface CategoryCardProps {
  category: CategoryInfo;
  topRepos?: { full_name: string; reepo_score: number | null }[];
}

export function CategoryCard({ category, topRepos }: CategoryCardProps) {
  return (
    <Link
      to={`/category/${category.slug}`}
      className="group flex flex-col rounded-lg border border-border/60 bg-card px-4 py-3 transition-all duration-150 hover:border-border/80 hover:bg-accent/5 hover:shadow-[0_2px_8px_-2px_rgba(0,0,0,0.08)] dark:hover:shadow-[0_2px_8px_-2px_rgba(0,0,0,0.3)]"
    >
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-medium text-foreground group-hover:underline underline-offset-2 truncate">
          {category.name}
        </span>
        <span className="font-mono text-[12px] text-muted-foreground tabular-nums">
          {category.repo_count}
        </span>
      </div>
      {topRepos && topRepos.length > 0 && (
        <div className="mt-2 space-y-1 border-t border-border/50 pt-2">
          {topRepos.slice(0, 3).map((r) => (
            <div key={r.full_name} className="flex items-center justify-between text-[11px]">
              <span className="truncate text-muted-foreground">{r.full_name}</span>
              {r.reepo_score !== null && (
                <span className="ml-2 shrink-0 font-mono tabular-nums" style={{ color: scoreColorVar(r.reepo_score) }}>
                  {r.reepo_score}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </Link>
  );
}
