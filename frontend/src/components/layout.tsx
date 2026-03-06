import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { SearchCommand } from '@/components/search-command';
import { ThemeToggle } from '@/components/theme-toggle';

const NAV_LINKS = [
  { to: '/search', label: 'Search' },
  { to: '/trending', label: 'Trending' },
  { to: '/category/frameworks', label: 'Categories' },
  { to: '/stats', label: 'Stats' },
  { to: '/pricing', label: 'Pricing' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <div className="flex h-14 items-center justify-between">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2 font-semibold text-foreground hover:opacity-70 transition-opacity">
                <span className="flex h-6 w-6 items-center justify-center rounded-md bg-foreground text-background font-mono text-xs font-bold">R</span>
                <span className="text-sm tracking-tight">Reepo</span>
              </Link>
              <nav className="hidden md:flex items-center gap-1">
                {NAV_LINKS.map(({ to, label }) => (
                  <Link
                    key={to}
                    to={to}
                    className="rounded-md px-3 py-1.5 text-[13px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  >
                    {label}
                  </Link>
                ))}
              </nav>
            </div>
            <div className="flex items-center gap-2">
              <div className="hidden md:block">
                <SearchCommand />
              </div>
              <ThemeToggle />
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden h-8 w-8"
                onClick={() => setMobileOpen(!mobileOpen)}
                aria-label="Toggle menu"
              >
                {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </Button>
            </div>
          </div>
        </div>
        {mobileOpen && (
          <div className="md:hidden border-t border-border bg-background">
            <div className="px-4 py-3 space-y-1">
              {NAV_LINKS.map(({ to, label }) => (
                <Link
                  key={to}
                  to={to}
                  className="block rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  onClick={() => setMobileOpen(false)}
                >
                  {label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="mt-20 border-t border-border">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 py-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span className="flex h-5 w-5 items-center justify-center rounded bg-foreground text-background font-mono text-[10px] font-bold">R</span>
              <span>Reepo.dev</span>
              <Separator orientation="vertical" className="h-3" />
              <span>Open source discovery for AI</span>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <a href="/api/open-data/latest.csv" className="hover:text-foreground transition-colors">Open Data</a>
              <Link to="/stats" className="hover:text-foreground transition-colors">Stats</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
