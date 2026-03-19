import { Link } from 'react-router-dom';
import type { CategoryInfo } from '@/lib/api';

interface CategoryCardProps {
  category: CategoryInfo;
  topRepos?: { full_name: string; owner: string }[];
}

export function CategoryCard({ category, topRepos }: CategoryCardProps) {
  return (
    <Link
      to={`/category/${category.slug}`}
      className="group flex flex-col rounded-lg border border-border/60 bg-card px-3.5 py-3 transition-all duration-150 hover:border-border/80 hover:bg-accent/5 hover:shadow-[0_2px_8px_-2px_rgba(0,0,0,0.08)] dark:hover:shadow-[0_2px_8px_-2px_rgba(0,0,0,0.3)]"
    >
      <div className="flex items-center">
        <span className="text-[13px] font-medium text-foreground group-hover:underline underline-offset-2 truncate">
          {category.name}
        </span>
      </div>
      {topRepos && topRepos.length > 0 && (
        <div className="mt-2 space-y-1.5 border-t border-border/50 pt-2">
          {topRepos.slice(0, 3).map((r) => (
            <div key={r.full_name} className="flex items-center gap-1.5 text-[11px]">
              <img
                src={`https://github.com/${r.owner}.png?size=16`}
                alt=""
                className="h-4 w-4 shrink-0 rounded-sm"
              />
              <span className="truncate text-muted-foreground">{r.full_name}</span>
            </div>
          ))}
        </div>
      )}
    </Link>
  );
}
