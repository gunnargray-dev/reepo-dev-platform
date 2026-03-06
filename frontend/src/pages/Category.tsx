import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { RepoCard } from '@/components/repo-card';
import { Pagination } from '@/components/pagination';
import type { Repo, CategoryInfo, TagInfo } from '@/lib/api';
import { searchRepos, getCategories, getCategoryTags } from '@/lib/api';

export default function Category() {
  const { slug } = useParams<{ slug: string }>();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [category, setCategory] = useState<CategoryInfo | null>(null);
  const [tags, setTags] = useState<TagInfo[]>([]);
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    setActiveTag(null);
    setPage(1);
    getCategories().then((cats) => {
      const cat = cats.find((c) => c.slug === slug);
      if (cat) { setCategory(cat); document.title = `${cat.name} -- Reepo.dev`; }
    });
    getCategoryTags(slug).then(setTags).catch(() => setTags([]));
  }, [slug]);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    searchRepos({
      q: activeTag || undefined,
      category: slug,
      sort: 'reepo_score',
      page,
      limit: 20,
    })
      .then((res) => { setRepos(res.repos); setTotal(res.total); setTotalPages(res.pages); })
      .catch(() => setRepos([]))
      .finally(() => setLoading(false));
  }, [slug, activeTag, page]);

  const handleTagClick = (tag: string) => {
    setPage(1);
    setActiveTag(activeTag === tag ? null : tag);
  };

  return (
    <div className="mx-auto max-w-3xl animate-fade-in px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold text-foreground">{category?.name || slug}</h1>
      {category?.description && <p className="mt-1 text-[14px] text-muted-foreground">{category.description}</p>}
      {!loading && <p className="mt-1 font-mono text-[13px] tabular-nums text-muted-foreground">{total} repos</p>}

      {tags.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {tags.map((t) => (
            <Badge
              key={t.tag}
              variant={activeTag === t.tag ? 'default' : 'secondary'}
              className="cursor-pointer select-none"
              onClick={() => handleTagClick(t.tag)}
            >
              {t.tag}
              <span className="ml-1 opacity-50">{t.count}</span>
            </Badge>
          ))}
        </div>
      )}

      <div className="mt-6">
        {loading ? (
          <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-[72px]" />)}</div>
        ) : repos.length === 0 ? (
          <div className="py-20 text-center">
            <h3 className="text-lg font-medium text-foreground mb-1">No repos found</h3>
            <p className="text-[14px] text-muted-foreground">
              {activeTag ? 'Try a different tag or clear the filter.' : 'Check back after the next crawl.'}
            </p>
            {activeTag && (
              <button
                onClick={() => { setActiveTag(null); setPage(1); }}
                className="mt-2 text-[13px] text-muted-foreground underline hover:text-foreground"
              >
                Clear filter
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="space-y-2">{repos.map((repo) => <RepoCard key={repo.id} repo={repo} />)}</div>
            <Pagination page={page} totalPages={totalPages} onPageChange={(p) => { setPage(p); window.scrollTo({ top: 0, behavior: 'smooth' }); }} />
          </>
        )}
      </div>
    </div>
  );
}
