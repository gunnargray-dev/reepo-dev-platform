import { Link } from 'react-router-dom';
import type { CategoryInfo } from '../lib/api';
import { categoryIcon } from '../lib/utils';

interface CategoryCardProps { category: CategoryInfo; }

export default function CategoryCard({ category }: CategoryCardProps) {
  return (
    <Link to={`/category/${category.slug}`} className="card p-4 flex items-center gap-3 group">
      <span className="text-2xl">{categoryIcon(category.slug)}</span>
      <div className="min-w-0">
        <h3 className="text-white font-medium text-sm group-hover:text-accent transition-colors truncate">{category.name}</h3>
        <p className="text-gray-500 text-xs mt-0.5">{category.repo_count} repos</p>
      </div>
    </Link>
  );
}
