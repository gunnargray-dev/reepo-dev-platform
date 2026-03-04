import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Search from './pages/Search';
import RepoDetail from './pages/RepoDetail';
import Category from './pages/Category';
import Trending from './pages/Trending';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/repo/:owner/:name" element={<RepoDetail />} />
        <Route path="/category/:slug" element={<Category />} />
        <Route path="/trending" element={<Trending />} />
      </Routes>
    </Layout>
  );
}
