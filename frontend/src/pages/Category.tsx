import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import RepoCard from '../components/RepoCard';
import Pagination from '../components/Pagination';
import type { Repo, CategoryInfo } from '../lib/api';
import { searchRepos, getCategories } from '../lib/api';
import { categoryIcon } from '../lib/utils';

export default function Category() {
  const { slug } = useParams<{ slug: string }>();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [category, setCategory] = useState<CategoryInfo | null>(null);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    getCategories().then((cats) => {
      const cat = cats.find((c) => c.slug === slug);
      if (cat) { setCategory(cat); document.title = `${cat.name} — Reepo.dev`; }
    });
  }, [slug]);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    searchRepos({ category: slug, sort: 'reepo_score', page, limit: 20 })
      .then((res) => { setRepos(res.repos); setTotal(res.total); setTotalPages(res.pages); })
      .catch(() => setRepos([]))
      .finally(() => setLoading(false));
  }, [slug, page]);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center gap-3 mb-2">
        {slug && <span className="text-3xl">{categoryIcon(slug)}</span>}
        <h1 className="text-2xl sm:text-3xl font-bold text-white">{category?.name || slug}</h1>
      </div>
      {category?.description && <p className="text-gray-400 mb-2">{category.description}</p>}
      {!loading && <p className="text-sm text-gray-500 mb-8">{total} repos</p>}

      {loading ? (
        <div className="space-y-3">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="card p-5 h-24 animate-pulse" />)}</div>
      ) : repos.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-4xl mb-4">📭</div>
          <h3 className="text-xl font-semibold text-white mb-2">No repos in this category yet</h3>
          <p className="text-gray-500">Check back after the next crawl.</p>
        </div>
      ) : (
        <>
          <div className="space-y-3">{repos.map((repo) => <RepoCard key={repo.id} repo={repo} />)}</div>
          <Pagination page={page} totalPages={totalPages} onPageChange={(p) => { setPage(p); window.scrollTo({ top: 0, behavior: 'smooth' }); }} />
        </>
      )}
    </div>
  );
}
