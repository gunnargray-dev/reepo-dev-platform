import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from '@/components/layout';
import Home from '@/pages/Home';

const Search = lazy(() => import('@/pages/Search'));
const RepoDetail = lazy(() => import('@/pages/RepoDetail'));
const Category = lazy(() => import('@/pages/Category'));
const Trending = lazy(() => import('@/pages/Trending'));
const Pricing = lazy(() => import('@/pages/Pricing'));
const Compare = lazy(() => import('@/pages/Compare'));
const Stats = lazy(() => import('@/pages/Stats'));
const Alternatives = lazy(() => import('@/pages/Alternatives'));
const AdminAnalytics = lazy(() => import('@/pages/AdminAnalytics'));
const About = lazy(() => import('@/pages/About'));
const SavedRepos = lazy(() => import('@/pages/SavedRepos'));
const SubmitRepo = lazy(() => import('@/pages/SubmitRepo'));
const Projects = lazy(() => import('@/pages/Projects'));
const SubmitProject = lazy(() => import('@/pages/SubmitProject'));
const Score = lazy(() => import('@/pages/Score'));
const CardVariants = lazy(() => import('@/pages/CardVariants'));
const LoadingVariants = lazy(() => import('@/pages/LoadingVariants'));

export default function App() {
  return (
    <Layout>
      <Suspense fallback={null}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/search" element={<Search />} />
          <Route path="/repo/:owner/:name" element={<RepoDetail />} />
          <Route path="/category/:slug" element={<Category />} />
          <Route path="/trending" element={<Trending />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/alternatives/:owner/:name" element={<Alternatives />} />
          <Route path="/about" element={<About />} />
          <Route path="/admin/analytics" element={<AdminAnalytics />} />
          <Route path="/saved" element={<SavedRepos />} />
          <Route path="/submit" element={<SubmitRepo />} />
          <Route path="/projects/new" element={<SubmitProject />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/score" element={<Score />} />
          <Route path="/card-variants" element={<CardVariants />} />
          <Route path="/loading-variants" element={<LoadingVariants />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}
