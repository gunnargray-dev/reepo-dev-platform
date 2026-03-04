import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import SearchBar from './SearchBar';
import NewsletterForm from './NewsletterForm';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const navLinks = [
    { to: '/search', label: 'Search' },
    { to: '/trending', label: 'Trending' },
    { to: '/category/frameworks', label: 'Categories' },
    { to: '/pricing', label: 'Pricing' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border-subtle">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2 text-xl font-bold text-white hover:text-accent transition-colors">
                <span className="bg-accent rounded-lg w-8 h-8 flex items-center justify-center text-white font-mono text-sm">R</span>
                <span>Reepo</span>
              </Link>
              <nav className="hidden md:flex items-center gap-6">
                {navLinks.map(({ to, label }) => (
                  <Link key={to} to={to} className="text-gray-400 hover:text-white text-sm font-medium transition-colors">
                    {label}
                  </Link>
                ))}
              </nav>
            </div>
            <div className="hidden md:block w-72">
              <SearchBar compact onSearch={(q: string) => navigate(`/search?q=${encodeURIComponent(q)}`)} />
            </div>
            <button
              className="md:hidden text-gray-400 hover:text-white p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border-subtle bg-bg-primary">
            <div className="px-4 py-3 space-y-3">
              <SearchBar compact onSearch={(q: string) => { navigate(`/search?q=${encodeURIComponent(q)}`); setMobileMenuOpen(false); }} />
              {navLinks.map(({ to, label }) => (
                <Link key={to} to={to} className="block text-gray-400 hover:text-white text-sm font-medium py-2" onClick={() => setMobileMenuOpen(false)}>
                  {label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-border-subtle py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="bg-accent rounded w-5 h-5 flex items-center justify-center text-white font-mono text-xs">R</span>
                  <span className="text-sm text-gray-400">Reepo.dev</span>
                </div>
                <p className="text-sm text-gray-500">Open source discovery engine for AI repos</p>
              </div>
              <NewsletterForm />
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
