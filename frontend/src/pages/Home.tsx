import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import CategoryCard from '../components/CategoryCard';
import RepoCard from '../components/RepoCard';
import type { CategoryInfo, Repo, StatsResponse } from '../lib/api';
import { getCategories, getTrending, getStats } from '../lib/api';
import { formatNumber } from '../lib/utils';

export default function Home() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [trending, setTrending] = useState<Repo[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = 'Reepo.dev — Discover Open Source AI';
    Promise.allSettled([getCategories(), getTrending('week', 6), getStats()]).then(([catR, trendR, statsR]) => {
      if (catR.status === 'fulfilled') setCategories(catR.value);
      if (trendR.status === 'fulfilled') setTrending(trendR.value);
      if (statsR.status === 'fulfilled') setStats(statsR.value);
      setLoading(false);
    });
  }, []);

  return (
    <div>
      <section className="py-20 sm:py-28 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl sm:text-6xl font-bold text-white tracking-tight">
            Discover open source <span className="text-accent">AI</span>
          </h1>
          <p className="mt-4 text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto">Search, score, save, share</p>
          <div className="mt-10">
            <SearchBar placeholder="Search 500+ AI repos..." onSearch={(q: string) => navigate(`/search?q=${encodeURIComponent(q)}`)} />
          </div>
          {stats && (
            <div className="mt-8 flex items-center justify-center gap-6 text-sm text-gray-500 flex-wrap">
              <span>{formatNumber(stats.total_repos)} repos indexed</span>
              <span className="w-1 h-1 rounded-full bg-gray-600" />
              <span>{Object.keys(stats.by_category).length} categories</span>
              <span className="w-1 h-1 rounded-full bg-gray-600" />
              <span>Avg score: {stats.score_stats.avg_score}</span>
            </div>
          )}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <h2 className="text-xl font-semibold text-white mb-6">Categories</h2>
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {Array.from({ length: 10 }).map((_, i) => <div key={i} className="card p-4 h-16 animate-pulse" />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {categories.map((cat) => <CategoryCard key={cat.slug} category={cat} />)}
          </div>
        )}
      </section>

      {trending.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Trending this week</h2>
            <button onClick={() => navigate('/trending')} className="text-sm text-accent hover:text-accent-hover transition-colors">View all →</button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {trending.map((repo) => <RepoCard key={repo.id} repo={repo} />)}
          </div>
        </section>
      )}
    </div>
  );
}
