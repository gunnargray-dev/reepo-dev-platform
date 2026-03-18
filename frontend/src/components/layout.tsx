import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X, LogOut, Bookmark, FolderPlus, Rocket, ChevronDown, User as UserIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { SearchCommand } from '@/components/search-command';
import { ThemeToggle } from '@/components/theme-toggle';
import { useAuth } from '@/lib/auth';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';


const NAV_LINKS = [
  { to: '/search', label: 'Search' },
  { to: '/projects', label: 'Projects' },
  { to: '/about', label: 'About' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, loading, signIn, signOut } = useAuth();

  const avatarUrl = user?.user_metadata?.avatar_url;

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <div className="flex h-14 items-center justify-between">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center hover:opacity-70 transition-opacity">
                <img src="/reepo-logo.svg" alt="Reepo" className="h-3.5 invert dark:invert-0" />
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
              {!loading && !user && (
                <Button variant="ghost" size="sm" onClick={signIn} className="text-[13px]">
                  Sign in with GitHub
                </Button>
              )}
              {user && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="flex items-center gap-1 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
                      {avatarUrl ? (
                        <img src={avatarUrl} alt="" className="h-7 w-7 rounded-full" />
                      ) : (
                        <div className="h-7 w-7 rounded-full bg-muted flex items-center justify-center">
                          <UserIcon className="h-4 w-4 text-muted-foreground" />
                        </div>
                      )}
                      <ChevronDown className="h-3 w-3 text-muted-foreground" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem asChild>
                      <Link to="/saved" className="flex items-center gap-2">
                        <Bookmark className="h-4 w-4" />
                        Saved Repos
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link to="/projects" className="flex items-center gap-2">
                        <Rocket className="h-4 w-4" />
                        My Projects
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link to="/submit" className="flex items-center gap-2">
                        <FolderPlus className="h-4 w-4" />
                        Submit a Repo
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={signOut} className="flex items-center gap-2">
                      <LogOut className="h-4 w-4" />
                      Sign Out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
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
              <Separator className="my-2" />
              {!loading && !user && (
                <button
                  onClick={() => { signIn(); setMobileOpen(false); }}
                  className="block w-full text-left rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  Sign in with GitHub
                </button>
              )}
              {user && (
                <>
                  <Link
                    to="/saved"
                    className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    onClick={() => setMobileOpen(false)}
                  >
                    <Bookmark className="h-4 w-4" />
                    Saved Repos
                  </Link>
                  <Link
                    to="/projects"
                    className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    onClick={() => setMobileOpen(false)}
                  >
                    <Rocket className="h-4 w-4" />
                    My Projects
                  </Link>
                  <Link
                    to="/submit"
                    className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    onClick={() => setMobileOpen(false)}
                  >
                    <FolderPlus className="h-4 w-4" />
                    Submit a Repo
                  </Link>
                  <Separator className="my-2" />
                  <button
                    onClick={() => { signOut(); setMobileOpen(false); }}
                    className="flex items-center gap-2 w-full rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign Out
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="mt-20 border-t border-border">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 py-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <img src="/reepo-logo.svg" alt="Reepo" className="h-2.5 invert dark:invert-0" />
              <Separator orientation="vertical" className="h-3" />
              <span>Open source discovery for AI</span>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <Link to="/about" className="hover:text-foreground transition-colors">How Scoring Works</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
