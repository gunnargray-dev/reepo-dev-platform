import { Routes, Route } from 'react-router-dom';
import Layout from '@/components/layout';
import Home from '@/pages/Home';
import Search from '@/pages/Search';
import RepoDetail from '@/pages/RepoDetail';
import Category from '@/pages/Category';
import Trending from '@/pages/Trending';
import Pricing from '@/pages/Pricing';
import Compare from '@/pages/Compare';
import Stats from '@/pages/Stats';
import Alternatives from '@/pages/Alternatives';
import AdminAnalytics from '@/pages/AdminAnalytics';
import About from '@/pages/About';
import SavedRepos from '@/pages/SavedRepos';
import SubmitRepo from '@/pages/SubmitRepo';
import Projects from '@/pages/Projects';
import SubmitProject from '@/pages/SubmitProject';
import Score from '@/pages/Score';
import CardVariants from '@/pages/CardVariants';

export default function App() {
  return (
    <Layout>
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
      </Routes>
    </Layout>
  );
}
