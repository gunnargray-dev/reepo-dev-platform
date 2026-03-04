import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Search from './pages/Search';
import RepoDetail from './pages/RepoDetail';
import Category from './pages/Category';
import Trending from './pages/Trending';
import Pricing from './pages/Pricing';
import Compare from './pages/Compare';
import Stats from './pages/Stats';
import AdminAnalytics from './pages/AdminAnalytics';

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
        <Route path="/admin/analytics" element={<AdminAnalytics />} />
      </Routes>
    </Layout>
  );
}
