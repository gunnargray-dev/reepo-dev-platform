import { Link } from 'react-router-dom';
import type { CategoryInfo } from '@/lib/api';

export function CategoryCard({ category }: { category: CategoryInfo }) {
  return (
    <Link
      to={`/category/${category.slug}`}
      className="group flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:border-border/80 hover:bg-accent/5"
    >
      <span className="text-[13px] font-medium text-foreground group-hover:underline underline-offset-2 truncate">
        {category.name}
      </span>
      <span className="font-mono text-[12px] text-muted-foreground tabular-nums">
        {category.repo_count}
      </span>
    </Link>
  );
}
