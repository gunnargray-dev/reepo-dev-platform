import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RepoCard } from '@/components/repo-card';
import { Pagination } from '@/components/pagination';
import type { Repo, CategoryInfo, TagInfo } from '@/lib/api';
import { searchRepos, getCategories, getCategoryTags } from '@/lib/api';

const SORT_OPTIONS = [
  { value: 'reepo_score', label: 'Score' },
  { value: 'stars', label: 'Stars' },
  { value: 'pushed_at', label: 'Recent' },
];

const LANGUAGES = ['Python', 'TypeScript', 'JavaScript', 'Go', 'Rust', 'C++', 'Java', 'C#', 'Swift', 'Jupyter Notebook'];

export default function Category() {
  const { slug } = useParams<{ slug: string }>();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [category, setCategory] = useState<CategoryInfo | null>(null);
  const [tags, setTags] = useState<TagInfo[]>([]);
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [language, setLanguage] = useState<string | null>(null);
  const [sort, setSort] = useState('reepo_score');
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const resultKey = useRef(0);

  useEffect(() => {
    if (!slug) return;
    setActiveTag(null);
    setLanguage(null);
    setSort('reepo_score');
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
      language: language || undefined,
      sort,
      page,
      limit: 20,
    })
      .then((res) => {
        setRepos(res.repos);
        setTotal(res.total);
        setTotalPages(res.pages);
        resultKey.current += 1;
      })
      .catch(() => setRepos([]))
      .finally(() => setLoading(false));
  }, [slug, activeTag, language, sort, page]);

  const resetPage = () => setPage(1);
  const hasFilters = activeTag || language;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <div className="flex items-start justify-between gap-4 animate-slide-up">
        <div>
          <h1 className="text-xl font-semibold text-foreground">{category?.name || slug}</h1>
          {category?.description && <p className="mt-1 text-[14px] text-muted-foreground">{category.description}</p>}
        </div>
        {!loading && <span className="shrink-0 font-mono text-[13px] tabular-nums text-muted-foreground mt-1">{total} repos</span>}
      </div>

      <div className="mt-4 flex items-center gap-1.5 flex-wrap animate-fade-in" style={{ animationDelay: '0.05s' }}>
        <Select value={sort} onValueChange={(v) => { setSort(v); resetPage(); }}>
          <SelectTrigger className="h-8 text-[13px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value} className="text-[13px]">{o.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={language || '_all'} onValueChange={(v) => { setLanguage(v === '_all' ? null : v); resetPage(); }}>
          <SelectTrigger className="h-8 text-[13px]">
            <SelectValue placeholder="Language" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="_all" className="text-[13px]">All languages</SelectItem>
            {LANGUAGES.map((l) => (
              <SelectItem key={l} value={l} className="text-[13px]">{l}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        {tags.length > 0 && (
          <Select value={activeTag || '_all'} onValueChange={(v) => { setActiveTag(v === '_all' ? null : v); resetPage(); }}>
            <SelectTrigger className="h-8 text-[13px]">
              <SelectValue placeholder="Topic" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="_all" className="text-[13px]">All topics</SelectItem>
              {tags.slice(0, 20).map((t) => (
                <SelectItem key={t.tag} value={t.tag} className="text-[13px]">
                  {t.tag} <span className="text-muted-foreground ml-1">({t.count})</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {hasFilters && (
          <Button
            variant="ghost"
            size="xs"
            className="text-[12px] text-muted-foreground"
            onClick={() => { setActiveTag(null); setLanguage(null); resetPage(); }}
          >
            <X className="h-3 w-3" />
            Clear
          </Button>
        )}
      </div>

      <div className="mt-5">
        {loading ? null : repos.length === 0 ? (
          <div className="py-20 text-center animate-fade-in">
            <h3 className="text-lg font-medium text-foreground mb-1">No repos found</h3>
            <p className="text-[14px] text-muted-foreground">
              {hasFilters ? 'Try adjusting your filters.' : 'Check back after the next crawl.'}
            </p>
            {hasFilters && (
              <button
                onClick={() => { setActiveTag(null); setLanguage(null); resetPage(); }}
                className="mt-2 text-[13px] text-muted-foreground underline hover:text-foreground"
              >
                Clear filters
              </button>
            )}
          </div>
        ) : (
          <div key={resultKey.current} className="animate-fade-in">
            <div className="space-y-2">{repos.map((repo) => <RepoCard key={repo.id} repo={repo} />)}</div>
            <Pagination page={page} totalPages={totalPages} onPageChange={(p) => { setPage(p); window.scrollTo({ top: 0, behavior: 'smooth' }); }} />
          </div>
        )}
      </div>
    </div>
  );
}
