# Frontend Rebuild Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the reepo.dev frontend with Tailwind v4, shadcn/ui, Geist font, and Linear-inspired monochromatic design.

**Architecture:** Delete all existing UI code (components, pages, CSS, tailwind config). Re-scaffold with Tailwind v4 + shadcn/ui. Rebuild every page using shadcn primitives. Keep lib/api.ts and route structure unchanged.

**Tech Stack:** React 18, Vite, Tailwind CSS v4, shadcn/ui, Geist + Geist Mono, next-themes, react-router-dom v6

---

### Task 1: Scaffold Tailwind v4 + shadcn/ui

**Files:**
- Delete: `tailwind.config.ts`, `postcss.config.js`, `src/index.css`, `src/lib/theme.tsx`
- Modify: `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`
- Create: `src/app/globals.css`, `components.json`

**Step 1: Remove old Tailwind v3 + PostCSS deps, install Tailwind v4 + shadcn deps**

Run:
```bash
cd /Users/gunnar/Documents/Dev/reepo-dev-platform/frontend
npm remove tailwindcss postcss autoprefixer
npm install tailwindcss@latest @tailwindcss/vite@latest
npm install next-themes class-variance-authority clsx tailwind-merge lucide-react
```

**Step 2: Delete old config files**

```bash
rm tailwind.config.ts postcss.config.js src/index.css src/lib/theme.tsx
```

**Step 3: Update vite.config.ts for Tailwind v4**

Replace contents with:
```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

**Step 4: Update tsconfig.json to add path aliases**

Replace contents with:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

**Step 5: Update index.html**

Replace with:
```html
<!DOCTYPE html>
<html lang="en" suppressHydrationWarning>
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Reepo.dev -- Open source discovery engine for AI repos. Search, score, and explore 500+ AI repositories." />
    <title>Reepo.dev -- Discover Open Source AI</title>
    <script>
      try {
        let theme = localStorage.getItem('theme');
        if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
          document.documentElement.classList.add('dark');
        }
      } catch (e) {}
    </script>
  </head>
  <body class="antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Step 6: Create globals.css with Tailwind v4 + shadcn theme**

Create `src/globals.css`:
```css
@import "tailwindcss";
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

@custom-variant dark (&:is(.dark *));

@theme {
  --font-sans: 'Geist', system-ui, -apple-system, sans-serif;
  --font-mono: 'Geist Mono', 'Menlo', monospace;

  --color-background: var(--bg);
  --color-foreground: var(--fg);
  --color-border: var(--border);
  --color-ring: var(--ring);

  --color-muted: var(--bg-muted);
  --color-muted-foreground: var(--fg-muted);

  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-fg);

  --color-card: var(--bg-subtle);
  --color-card-foreground: var(--fg);

  --color-primary: var(--accent);
  --color-primary-foreground: var(--accent-fg);

  --color-secondary: var(--bg-muted);
  --color-secondary-foreground: var(--fg);

  --color-destructive: #dc2626;
  --color-destructive-foreground: #ffffff;

  --color-popover: var(--bg);
  --color-popover-foreground: var(--fg);

  --color-input: var(--border);

  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.625rem;
  --radius-xl: 0.75rem;

  --animate-fade-in: fade-in 0.3s ease-out;
  --animate-slide-up: slide-up 0.3s ease-out;
}

:root {
  --bg: #ffffff;
  --bg-subtle: #fafafa;
  --bg-muted: #f4f4f5;
  --fg: #09090b;
  --fg-muted: #71717a;
  --fg-subtle: #a1a1aa;
  --border: #e4e4e7;
  --border-hover: #d4d4d8;
  --accent: #18181b;
  --accent-fg: #ffffff;
  --ring: #a1a1aa;
  --score-high: #16a34a;
  --score-mid: #ca8a04;
  --score-low: #dc2626;
}

.dark {
  --bg: #09090b;
  --bg-subtle: #111113;
  --bg-muted: #1c1c21;
  --fg: #fafafa;
  --fg-muted: #a1a1aa;
  --fg-subtle: #52525b;
  --border: #27272a;
  --border-hover: #3f3f46;
  --accent: #fafafa;
  --accent-fg: #09090b;
  --ring: #3f3f46;
  --score-high: #4ade80;
  --score-mid: #fbbf24;
  --score-low: #f87171;
}

body {
  background-color: var(--bg);
  color: var(--fg);
}

::selection {
  background: var(--accent);
  color: var(--accent-fg);
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
```

**Step 7: Create lib/cn.ts utility**

Create `src/lib/cn.ts`:
```ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Step 8: Update lib/utils.ts**

Keep existing functions. Update `scoreColorVar` and `scoreColor`:
```ts
export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Unknown';
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  const years = Math.floor(months / 12);
  return `${years}y ago`;
}

export function scoreColorVar(score: number | null): string {
  if (score === null) return 'var(--fg-subtle)';
  if (score >= 80) return 'var(--score-high)';
  if (score >= 50) return 'var(--score-mid)';
  return 'var(--score-low)';
}

export function scoreColor(score: number | null): React.CSSProperties {
  return { color: scoreColorVar(score) };
}

const LANGUAGE_COLORS: Record<string, string> = {
  Python: '#3572A5', JavaScript: '#f1e05a', TypeScript: '#3178c6',
  Rust: '#dea584', Go: '#00ADD8', 'C++': '#f34b7d', C: '#555555',
  Java: '#b07219', 'C#': '#178600', Ruby: '#701516', Swift: '#F05138',
  Kotlin: '#A97BFF', Jupyter: '#DA5B0B', Scala: '#c22d40', R: '#198CE7',
  Lua: '#000080', Shell: '#89e051',
};

export function languageColor(lang: string | null): string {
  if (!lang) return '#71717a';
  return LANGUAGE_COLORS[lang] || '#71717a';
}
```

**Step 9: Update main.tsx**

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from 'next-themes';
import App from './App';
import './globals.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <App />
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
```

**Step 10: Verify build compiles**

Run: `cd /Users/gunnar/Documents/Dev/reepo-dev-platform/frontend && npx tsc --noEmit`

At this point the app will not render (components deleted) but TypeScript should compile for the foundation files.

**Step 11: Commit**

```bash
git add -A
git commit -m "chore: scaffold Tailwind v4 + shadcn/ui foundation"
```

---

### Task 2: shadcn/ui primitives

**Files:**
- Create: `components.json`
- Create: `src/components/ui/button.tsx`
- Create: `src/components/ui/badge.tsx`
- Create: `src/components/ui/card.tsx`
- Create: `src/components/ui/input.tsx`
- Create: `src/components/ui/separator.tsx`
- Create: `src/components/ui/skeleton.tsx`
- Create: `src/components/ui/table.tsx`
- Create: `src/components/ui/tabs.tsx`
- Create: `src/components/ui/dialog.tsx`
- Create: `src/components/ui/command.tsx`
- Create: `src/components/ui/select.tsx`
- Create: `src/components/ui/slider.tsx`
- Create: `src/components/ui/radio-group.tsx`

**Step 1: Init shadcn**

Run:
```bash
cd /Users/gunnar/Documents/Dev/reepo-dev-platform/frontend
npx shadcn@latest init
```

When prompted:
- Style: New York
- Base color: Zinc
- CSS variables: yes
- CSS file: src/globals.css
- Tailwind config: (skip, v4)
- Components alias: @/components
- Utils alias: @/lib/cn
- React Server Components: no

If `shadcn init` overwrites globals.css, restore the version from Task 1 Step 6 (our custom theme variables must be preserved). The shadcn init may add its own CSS variable block -- merge carefully, keeping our `--bg`, `--fg`, `--border`, `--accent` scheme and mapping them to shadcn's expected `--background`, `--foreground`, etc. via the `@theme` block.

**Step 2: Add shadcn components**

Run each:
```bash
npx shadcn@latest add button badge card input separator skeleton table tabs dialog command select slider radio-group
```

**Step 3: Verify components installed**

Run: `ls src/components/ui/`

Expected: All component files listed above should exist.

**Step 4: Install cmdk if not already present (required by command component)**

Run: `npm install cmdk`

**Step 5: Commit**

```bash
git add -A
git commit -m "chore: add shadcn/ui primitive components"
```

---

### Task 3: Layout + Theme Toggle

**Files:**
- Delete: `src/components/Layout.tsx`, `src/components/SearchBar.tsx`
- Create: `src/components/layout.tsx`
- Create: `src/components/search-command.tsx`
- Create: `src/components/theme-toggle.tsx`

**Step 1: Create theme-toggle.tsx**

```tsx
import { useTheme } from 'next-themes';
import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      className="h-8 w-8 text-muted-foreground"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      aria-label="Toggle theme"
    >
      <Sun className="h-4 w-4 rotate-0 scale-100 transition-transform dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-transform dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
```

**Step 2: Create search-command.tsx**

```tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
} from '@/components/ui/command';

export function SearchCommand() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const handleSearch = () => {
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      setOpen(false);
      setQuery('');
    }
  };

  return (
    <>
      <Button
        variant="outline"
        className="relative h-8 w-56 justify-start rounded-md border-border bg-transparent text-sm text-muted-foreground"
        onClick={() => setOpen(true)}
      >
        <Search className="mr-2 h-3.5 w-3.5" />
        <span>Search repos...</span>
        <kbd className="pointer-events-none absolute right-1.5 hidden h-5 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput
          placeholder="Search repos..."
          value={query}
          onValueChange={setQuery}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSearch();
          }}
        />
        <CommandList>
          <CommandEmpty>
            {query ? (
              <button
                onClick={handleSearch}
                className="w-full py-6 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Search for "{query}" →
              </button>
            ) : (
              <p className="py-6 text-sm text-muted-foreground">Type to search repos...</p>
            )}
          </CommandEmpty>
        </CommandList>
      </CommandDialog>
    </>
  );
}
```

**Step 3: Create layout.tsx**

```tsx
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
```

**Step 4: Update App.tsx imports**

```tsx
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
import AdminAnalytics from '@/pages/AdminAnalytics';

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
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add layout with command-K search and theme toggle"
```

---

### Task 4: Shared custom components

**Files:**
- Delete: `src/components/ScoreBadge.tsx`, `src/components/RepoCard.tsx`, `src/components/CategoryCard.tsx`, `src/components/Pagination.tsx`, `src/components/NewsletterForm.tsx`
- Create: `src/components/score-badge.tsx`
- Create: `src/components/repo-card.tsx`
- Create: `src/components/category-card.tsx`
- Create: `src/components/pagination.tsx`
- Create: `src/components/stat-card.tsx`
- Create: `src/components/dimension-bar.tsx`

**Step 1: Create score-badge.tsx**

```tsx
import { cn } from '@/lib/cn';
import { scoreColorVar } from '@/lib/utils';

interface ScoreBadgeProps {
  score: number | null;
  size?: 'sm' | 'md' | 'lg';
}

export function ScoreBadge({ score, size = 'sm' }: ScoreBadgeProps) {
  const sizes = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-14 w-14 text-lg',
  };

  const color = scoreColorVar(score);

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-md font-mono font-semibold',
        sizes[size],
      )}
      style={{
        color,
        backgroundColor: score !== null
          ? `color-mix(in srgb, ${color} 12%, transparent)`
          : 'var(--bg-muted)',
      }}
    >
      {score ?? '--'}
    </span>
  );
}
```

**Step 2: Create dimension-bar.tsx**

```tsx
import { scoreColorVar } from '@/lib/utils';

interface DimensionBarProps {
  label: string;
  value: number;
}

export function DimensionBar({ label, value }: DimensionBarProps) {
  const color = scoreColorVar(value);

  return (
    <div className="flex items-center gap-3">
      <span className="w-24 shrink-0 text-[13px] text-muted-foreground">{label}</span>
      <div className="relative h-1.5 flex-1 rounded-full bg-muted">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
      <span
        className="w-7 text-right font-mono text-[13px] tabular-nums"
        style={{ color }}
      >
        {value}
      </span>
    </div>
  );
}
```

**Step 3: Create repo-card.tsx**

```tsx
import { Link } from 'react-router-dom';
import { Star, GitFork } from 'lucide-react';
import type { Repo } from '@/lib/api';
import { formatNumber, timeAgo, languageColor } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { ScoreBadge } from '@/components/score-badge';

interface RepoCardProps {
  repo: Repo;
  showDelta?: number;
}

export function RepoCard({ repo, showDelta }: RepoCardProps) {
  return (
    <Link
      to={`/repo/${repo.owner}/${repo.name}`}
      className="group flex items-start justify-between gap-3 rounded-lg border border-border bg-card px-4 py-3.5 transition-colors hover:border-border/80 hover:bg-accent/5"
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-[14px] font-medium text-foreground group-hover:underline underline-offset-2 truncate">
            {repo.full_name}
          </h3>
          {repo.category_primary && (
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
              {repo.category_primary}
            </Badge>
          )}
        </div>
        {repo.description && (
          <p className="mt-1 text-[13px] text-muted-foreground line-clamp-1">{repo.description}</p>
        )}
        <div className="mt-2 flex items-center gap-3.5 text-[12px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Star className="h-3 w-3" />
            {formatNumber(repo.stars)}
            {showDelta !== undefined && showDelta > 0 && (
              <span style={{ color: 'var(--score-high)' }}>+{formatNumber(showDelta)}</span>
            )}
          </span>
          <span className="flex items-center gap-1">
            <GitFork className="h-3 w-3" />
            {formatNumber(repo.forks)}
          </span>
          {repo.language && (
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: languageColor(repo.language) }} />
              {repo.language}
            </span>
          )}
          {repo.pushed_at && <span>{timeAgo(repo.pushed_at)}</span>}
        </div>
      </div>
      <div className="shrink-0">
        <ScoreBadge score={repo.reepo_score} />
      </div>
    </Link>
  );
}
```

**Step 4: Create category-card.tsx**

```tsx
import { Link } from 'react-router-dom';
import type { CategoryInfo } from '@/lib/api';

export function CategoryCard({ category }: { category: CategoryInfo }) {
  return (
    <Link
      to={`/category/${category.slug}`}
      className="group flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:border-border/80 hover:bg-accent/5"
    >
      <span className="text-[13px] font-medium text-foreground group-hover:underline underline-offset-2 truncate">
        {category.name}
      </span>
      <span className="font-mono text-[12px] text-muted-foreground tabular-nums">
        {category.repo_count}
      </span>
    </Link>
  );
}
```

**Step 5: Create pagination.tsx**

```tsx
import { Button } from '@/components/ui/button';

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages: (number | '...')[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push('...');
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) pages.push(i);
    if (page < totalPages - 2) pages.push('...');
    pages.push(totalPages);
  }

  return (
    <div className="mt-8 flex items-center justify-center gap-1">
      <Button variant="ghost" size="sm" onClick={() => onPageChange(page - 1)} disabled={page <= 1} className="text-[13px]">
        Prev
      </Button>
      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`dots-${i}`} className="px-1.5 text-[13px] text-muted-foreground">...</span>
        ) : (
          <Button
            key={p}
            variant={p === page ? 'default' : 'ghost'}
            size="sm"
            className="h-8 w-8 font-mono text-[13px]"
            onClick={() => onPageChange(p as number)}
          >
            {p}
          </Button>
        )
      )}
      <Button variant="ghost" size="sm" onClick={() => onPageChange(page + 1)} disabled={page >= totalPages} className="text-[13px]">
        Next
      </Button>
    </div>
  );
}
```

**Step 6: Create stat-card.tsx**

```tsx
import { Card, CardContent } from '@/components/ui/card';

interface StatCardProps {
  label: string;
  value: string;
}

export function StatCard({ label, value }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xl font-semibold font-mono tabular-nums text-foreground">{value}</div>
        <div className="mt-0.5 text-[12px] text-muted-foreground">{label}</div>
      </CardContent>
    </Card>
  );
}
```

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: add shared custom components (repo card, score badge, dimension bar, etc)"
```

---

### Task 5: Home page

**Files:**
- Delete: `src/pages/Home.tsx`
- Create: `src/pages/Home.tsx`

**Step 1: Create Home.tsx**

```tsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { CategoryCard } from '@/components/category-card';
import { RepoCard } from '@/components/repo-card';
import type { CategoryInfo, Repo, StatsResponse } from '@/lib/api';
import { getCategories, getTrending, getStats } from '@/lib/api';
import { formatNumber } from '@/lib/utils';

export default function Home() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [trending, setTrending] = useState<Repo[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = 'Reepo.dev -- Discover Open Source AI';
    Promise.allSettled([getCategories(), getTrending('week', 6), getStats()]).then(([catR, trendR, statsR]) => {
      if (catR.status === 'fulfilled') setCategories(catR.value);
      if (trendR.status === 'fulfilled') setTrending(trendR.value);
      if (statsR.status === 'fulfilled') setStats(statsR.value);
      setLoading(false);
    });
  }, []);

  return (
    <div className="animate-fade-in">
      <section className="px-4 py-20 sm:py-28">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-5xl leading-[1.1]">
            Discover open source AI
          </h1>
          <p className="mt-3 text-[15px] text-muted-foreground">
            Search, score, and explore the best AI repositories
          </p>
          <div className="mt-8 flex justify-center">
            <Button
              variant="outline"
              className="h-11 w-full max-w-md justify-start rounded-lg border-border text-muted-foreground"
              onClick={() => {
                // Trigger Cmd+K
                document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
              }}
            >
              <Search className="mr-2 h-4 w-4" />
              <span>Search repos...</span>
              <kbd className="pointer-events-none ml-auto hidden h-5 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:flex">
                <span className="text-xs">⌘</span>K
              </kbd>
            </Button>
          </div>
          {stats && (
            <div className="mt-6 flex items-center justify-center gap-3 text-[13px] text-muted-foreground">
              <span className="font-mono tabular-nums">{formatNumber(stats.total_repos)}</span>
              <span>repos</span>
              <span className="text-border">/</span>
              <span className="font-mono tabular-nums">{Object.keys(stats.by_category).length}</span>
              <span>categories</span>
              <span className="text-border">/</span>
              <span>avg score <span className="font-mono tabular-nums">{stats.score_stats.avg_score}</span></span>
            </div>
          )}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 pb-14 sm:px-6">
        <h2 className="mb-4 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Categories</h2>
        {loading ? (
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
            {Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-11" />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
            {categories.map((cat) => <CategoryCard key={cat.slug} category={cat} />)}
          </div>
        )}
      </section>

      {trending.length > 0 && (
        <section className="mx-auto max-w-5xl px-4 pb-14 sm:px-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Trending this week</h2>
            <button
              onClick={() => navigate('/trending')}
              className="text-[13px] text-muted-foreground transition-colors hover:text-foreground"
            >
              View all &rarr;
            </button>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {trending.map((repo) => <RepoCard key={repo.id} repo={repo} />)}
          </div>
        </section>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A
git commit -m "feat: rebuild Home page"
```

---

### Task 6: Search page

**Files:**
- Delete: `src/pages/Search.tsx`
- Create: `src/pages/Search.tsx`

**Step 1: Create Search.tsx**

```tsx
import { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Slider } from '@/components/ui/slider';
import { RepoCard } from '@/components/repo-card';
import { Pagination } from '@/components/pagination';
import type { Repo, CategoryInfo, StatsResponse } from '@/lib/api';
import { searchRepos, getCategories, getStats } from '@/lib/api';

const SORT_OPTIONS = [
  { value: 'stars', label: 'Stars' },
  { value: 'reepo_score', label: 'Score' },
  { value: 'updated_at', label: 'Newest' },
  { value: 'name', label: 'Name' },
];

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const q = searchParams.get('q') || '';
  const category = searchParams.get('category') || '';
  const language = searchParams.get('language') || '';
  const sort = searchParams.get('sort') || 'stars';
  const minScore = parseInt(searchParams.get('min_score') || '0', 10);
  const page = parseInt(searchParams.get('page') || '1', 10);

  const [repos, setRepos] = useState<Repo[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    document.title = q ? `"${q}" -- Search -- Reepo.dev` : 'Search -- Reepo.dev';
  }, [q]);

  useEffect(() => {
    Promise.allSettled([getCategories(), getStats()]).then(([catR, statsR]) => {
      if (catR.status === 'fulfilled') setCategories(catR.value);
      if (statsR.status === 'fulfilled') setLanguages(Object.keys((statsR.value as StatsResponse).by_language));
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    searchRepos({ q, category, language, min_score: minScore || undefined, sort, page, limit: 20 })
      .then((res) => { setRepos(res.repos); setTotal(res.total); setTotalPages(res.pages); })
      .catch(() => { setRepos([]); setTotal(0); setTotalPages(0); })
      .finally(() => setLoading(false));
  }, [q, category, language, sort, minScore, page]);

  const updateParam = useCallback((key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value); else next.delete(key);
    next.delete('page');
    setSearchParams(next);
  }, [searchParams, setSearchParams]);

  const handlePageChange = useCallback((p: number) => {
    const next = new URLSearchParams(searchParams);
    next.set('page', String(p));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [searchParams, setSearchParams]);

  return (
    <div className="mx-auto max-w-5xl animate-fade-in px-4 py-8 sm:px-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">{q ? `Results for "${q}"` : 'All Repos'}</h1>
          {!loading && <p className="mt-0.5 font-mono text-[13px] tabular-nums text-muted-foreground">{total} repos</p>}
        </div>
        <Button variant="outline" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(!sidebarOpen)}>
          <SlidersHorizontal className="mr-2 h-3.5 w-3.5" />
          Filters
        </Button>
      </div>

      <div className="flex gap-8">
        <aside className={`${sidebarOpen ? 'block' : 'hidden'} w-full shrink-0 lg:block lg:w-48`}>
          <Card className="sticky top-20">
            <CardContent className="space-y-5 p-4">
              <div>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Category</h3>
                <div className="max-h-48 space-y-0.5 overflow-y-auto">
                  <label className="flex cursor-pointer items-center gap-2 py-0.5 text-[13px] text-muted-foreground hover:text-foreground">
                    <input type="radio" name="category" checked={!category} onChange={() => updateParam('category', '')} className="accent-foreground" /> All
                  </label>
                  {categories.map((cat) => (
                    <label key={cat.slug} className="flex cursor-pointer items-center gap-2 py-0.5 text-[13px] text-muted-foreground hover:text-foreground">
                      <input type="radio" name="category" checked={category === cat.slug} onChange={() => updateParam('category', cat.slug)} className="accent-foreground" />
                      <span className="truncate">{cat.name}</span>
                      <span className="ml-auto font-mono text-[11px] text-muted-foreground">{cat.repo_count}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Language</h3>
                <Select value={language || 'all'} onValueChange={(v) => updateParam('language', v === 'all' ? '' : v)}>
                  <SelectTrigger className="h-8 text-[13px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    {languages.map((lang) => <SelectItem key={lang} value={lang}>{lang}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  Min score <span className="font-mono text-foreground">{minScore}</span>
                </h3>
                <Slider
                  value={[minScore]}
                  onValueChange={([v]) => updateParam('min_score', v === 0 ? '' : String(v))}
                  min={0} max={100} step={5}
                />
              </div>
              <div>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Sort</h3>
                <Select value={sort} onValueChange={(v) => updateParam('sort', v)}>
                  <SelectTrigger className="h-8 text-[13px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {SORT_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </aside>

        <div className="min-w-0 flex-1">
          {loading ? (
            <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-[72px]" />)}</div>
          ) : repos.length === 0 ? (
            <div className="py-20 text-center">
              <h3 className="text-lg font-medium text-foreground mb-1">No repos found</h3>
              <p className="mb-4 text-[14px] text-muted-foreground">Try a different search or adjust filters.</p>
              <Button onClick={() => navigate('/search')}>Clear filters</Button>
            </div>
          ) : (
            <>
              <div className="space-y-2">{repos.map((repo) => <RepoCard key={repo.id} repo={repo} />)}</div>
              <Pagination page={page} totalPages={totalPages} onPageChange={handlePageChange} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A
git commit -m "feat: rebuild Search page with shadcn filters"
```

---

### Task 7: Repo Detail page

**Files:**
- Delete: `src/pages/RepoDetail.tsx`
- Create: `src/pages/RepoDetail.tsx`

**Step 1: Create RepoDetail.tsx**

```tsx
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Star, GitFork, ExternalLink, Copy, Check, AlertCircle } from 'lucide-react';
import type { Repo } from '@/lib/api';
import { getRepo, getSimilarRepos } from '@/lib/api';
import { formatNumber, timeAgo, languageColor, scoreColorVar } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { RepoCard } from '@/components/repo-card';
import { DimensionBar } from '@/components/dimension-bar';

const DIMENSIONS: Record<string, string> = {
  maintenance_health: 'Maintenance',
  documentation_quality: 'Documentation',
  community_activity: 'Community',
  popularity: 'Popularity',
  freshness: 'Freshness',
  license_score: 'License',
};

export default function RepoDetail() {
  const { owner, name } = useParams<{ owner: string; name: string }>();
  const [repo, setRepo] = useState<Repo | null>(null);
  const [similar, setSimilar] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!owner || !name) return;
    setLoading(true);
    document.title = `${owner}/${name} -- Reepo.dev`;
    Promise.allSettled([getRepo(owner, name), getSimilarRepos(owner, name)]).then(([rr, sr]) => {
      if (rr.status === 'fulfilled') setRepo(rr.value);
      if (sr.status === 'fulfilled') setSimilar(sr.value);
      setLoading(false);
    });
  }, [owner, name]);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  if (loading) return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="space-y-4">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="mt-4 h-48" />
      </div>
    </div>
  );

  if (!repo) return (
    <div className="mx-auto max-w-3xl px-4 py-20 text-center sm:px-6">
      <AlertCircle className="mx-auto h-10 w-10 text-muted-foreground" />
      <h1 className="mt-4 text-xl font-semibold text-foreground">Repo not found</h1>
      <p className="mt-1 text-[14px] text-muted-foreground">{owner}/{name} is not in our index.</p>
      <Button asChild className="mt-4">
        <Link to="/search">Search repos</Link>
      </Button>
    </div>
  );

  const scoreColor = scoreColorVar(repo.reepo_score);

  return (
    <div className="mx-auto max-w-3xl animate-fade-in px-4 py-8 sm:px-6">
      {/* Header */}
      <div className="flex items-start gap-3">
        <img
          src={`https://github.com/${repo.owner}.png?size=40`}
          alt=""
          className="h-10 w-10 rounded-lg"
        />
        <div className="min-w-0">
          <h1 className="text-xl font-semibold text-foreground truncate">{repo.full_name}</h1>
          {repo.description && (
            <p className="mt-1 text-[15px] leading-relaxed text-muted-foreground">{repo.description}</p>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 flex items-center gap-2">
        <Button asChild size="sm">
          <a href={repo.url} target="_blank" rel="noopener noreferrer">
            GitHub <ExternalLink className="ml-1.5 h-3 w-3" />
          </a>
        </Button>
        {repo.homepage && (
          <Button asChild variant="outline" size="sm">
            <a href={repo.homepage} target="_blank" rel="noopener noreferrer">Website</a>
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={handleShare}>
          {copied ? <><Check className="mr-1.5 h-3 w-3" />Copied</> : <><Copy className="mr-1.5 h-3 w-3" />Share</>}
        </Button>
      </div>

      {/* Meta */}
      <div className="mt-5 flex flex-wrap items-center gap-4 text-[13px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <Star className="h-3.5 w-3.5" />
          <strong className="font-medium text-foreground">{formatNumber(repo.stars)}</strong>
        </span>
        <span className="flex items-center gap-1">
          <GitFork className="h-3.5 w-3.5" />
          <strong className="font-medium text-foreground">{formatNumber(repo.forks)}</strong>
        </span>
        <span>{formatNumber(repo.open_issues)} issues</span>
        {repo.license && <span>{repo.license}</span>}
        {repo.language && (
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: languageColor(repo.language) }} />
            {repo.language}
          </span>
        )}
        {repo.created_at && <span>{timeAgo(repo.created_at)}</span>}
      </div>

      {/* Score */}
      <Card className="mt-8">
        <CardContent className="p-6">
          <div className="flex items-start gap-8">
            <div className="shrink-0 text-center">
              <div className="text-4xl font-bold font-mono tabular-nums" style={{ color: scoreColor }}>
                {repo.reepo_score ?? '--'}
              </div>
              <div className="mt-1 text-[12px] text-muted-foreground">/ 100</div>
            </div>
            {repo.score_breakdown && (
              <>
                <Separator orientation="vertical" className="h-auto self-stretch" />
                <div className="flex-1 space-y-2.5">
                  {Object.entries(repo.score_breakdown).map(([key, value]) => (
                    <DimensionBar key={key} label={DIMENSIONS[key] || key} value={value} />
                  ))}
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Topics */}
      {repo.topics && repo.topics.length > 0 && (
        <div className="mt-6">
          <h2 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Topics</h2>
          <div className="flex flex-wrap gap-1.5">
            {repo.topics.map((topic) => (
              <Badge key={topic} variant="secondary" asChild>
                <Link to={`/search?q=${encodeURIComponent(topic)}`}>{topic}</Link>
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Similar */}
      {similar.length > 0 && (
        <div className="mt-12">
          <h2 className="mb-4 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Similar repos</h2>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {similar.map((r) => <RepoCard key={r.id} repo={r} />)}
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A
git commit -m "feat: rebuild RepoDetail page with score grid"
```

---

### Task 8: Category + Trending pages

**Files:**
- Delete: `src/pages/Category.tsx`, `src/pages/Trending.tsx`
- Create: `src/pages/Category.tsx`, `src/pages/Trending.tsx`

**Step 1: Create Category.tsx**

```tsx
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';
import { RepoCard } from '@/components/repo-card';
import { Pagination } from '@/components/pagination';
import type { Repo, CategoryInfo } from '@/lib/api';
import { searchRepos, getCategories } from '@/lib/api';

export default function Category() {
  const { slug } = useParams<{ slug: string }>();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [category, setCategory] = useState<CategoryInfo | null>(null);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    getCategories().then((cats) => {
      const cat = cats.find((c) => c.slug === slug);
      if (cat) { setCategory(cat); document.title = `${cat.name} -- Reepo.dev`; }
    });
  }, [slug]);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    searchRepos({ category: slug, sort: 'reepo_score', page, limit: 20 })
      .then((res) => { setRepos(res.repos); setTotal(res.total); setTotalPages(res.pages); })
      .catch(() => setRepos([]))
      .finally(() => setLoading(false));
  }, [slug, page]);

  return (
    <div className="mx-auto max-w-3xl animate-fade-in px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold text-foreground">{category?.name || slug}</h1>
      {category?.description && <p className="mt-1 text-[14px] text-muted-foreground">{category.description}</p>}
      {!loading && <p className="mt-1 font-mono text-[13px] tabular-nums text-muted-foreground">{total} repos</p>}

      <div className="mt-6">
        {loading ? (
          <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-[72px]" />)}</div>
        ) : repos.length === 0 ? (
          <div className="py-20 text-center">
            <h3 className="text-lg font-medium text-foreground mb-1">No repos in this category yet</h3>
            <p className="text-[14px] text-muted-foreground">Check back after the next crawl.</p>
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
```

**Step 2: Create Trending.tsx**

```tsx
import { useEffect, useState } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RepoCard } from '@/components/repo-card';
import type { TrendingRepo, Repo } from '@/lib/api';
import { getTrending, searchRepos } from '@/lib/api';

type Period = 'day' | 'week' | 'month';

export default function Trending() {
  const [period, setPeriod] = useState<Period>('week');
  const [trending, setTrending] = useState<TrendingRepo[]>([]);
  const [newRepos, setNewRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { document.title = 'Trending -- Reepo.dev'; }, []);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([getTrending(period, 20), searchRepos({ sort: 'updated_at', limit: 6 })]).then(([tr, nr]) => {
      if (tr.status === 'fulfilled') setTrending(tr.value);
      if (nr.status === 'fulfilled') setNewRepos(nr.value.repos);
      setLoading(false);
    });
  }, [period]);

  return (
    <div className="mx-auto max-w-3xl animate-fade-in px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold text-foreground mb-6">Trending</h1>

      <Tabs value={period} onValueChange={(v) => setPeriod(v as Period)} className="mb-6">
        <TabsList>
          <TabsTrigger value="day">Day</TabsTrigger>
          <TabsTrigger value="week">Week</TabsTrigger>
          <TabsTrigger value="month">Month</TabsTrigger>
        </TabsList>
      </Tabs>

      {loading ? (
        <div className="space-y-2">{Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-[72px]" />)}</div>
      ) : trending.length === 0 ? (
        <div className="py-20 text-center">
          <h3 className="text-lg font-medium text-foreground mb-1">No trending data yet</h3>
          <p className="text-[14px] text-muted-foreground">Trending data appears after multiple crawl cycles.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {trending.map((repo, index) => (
            <div key={repo.id} className="flex items-center gap-3">
              <span className="w-6 shrink-0 text-right font-mono text-[13px] tabular-nums text-muted-foreground">{index + 1}</span>
              <div className="min-w-0 flex-1"><RepoCard repo={repo} showDelta={repo.star_delta} /></div>
            </div>
          ))}
        </div>
      )}

      {newRepos.length > 0 && (
        <div className="mt-14">
          <h2 className="mb-4 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Recently indexed</h2>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {newRepos.map((repo) => <RepoCard key={repo.id} repo={repo} />)}
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: rebuild Category and Trending pages"
```

---

### Task 9: Compare + Stats pages

**Files:**
- Delete: `src/pages/Compare.tsx`, `src/pages/Stats.tsx`
- Create: `src/pages/Compare.tsx`, `src/pages/Stats.tsx`

**Step 1: Create Compare.tsx**

```tsx
import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { formatNumber, scoreColorVar } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScoreBadge } from '@/components/score-badge';

interface CompareRepo {
  id: number;
  full_name: string;
  stars: number;
  forks: number;
  language: string;
  license: string;
  reepo_score: number;
  score_breakdown: Record<string, number>;
  open_issues: number;
  pushed_at: string;
  category_primary: string;
}

export default function Compare() {
  const [params] = useSearchParams();
  const [repos, setRepos] = useState<CompareRepo[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const ids = params.get('ids') || '';

  useEffect(() => {
    document.title = 'Compare -- Reepo.dev';
    if (!ids) { setLoading(false); setError('Add ?ids=1,2,3 to compare repos'); return; }
    fetch(`/api/compare?repo_ids=${ids}&user_id=1`, { method: 'POST' })
      .then((r) => {
        if (r.status === 403) throw new Error('pro_required');
        if (!r.ok) throw new Error('failed');
        return r.json();
      })
      .then((data) => setRepos(data.repos))
      .catch((e) => setError(e.message === 'pro_required' ? 'pro_required' : 'Could not load comparison'))
      .finally(() => setLoading(false));
  }, [ids]);

  if (loading) return <div className="mx-auto max-w-4xl px-4 py-12"><Skeleton className="h-64" /></div>;

  if (error === 'pro_required') return (
    <div className="mx-auto max-w-3xl animate-fade-in px-4 py-20 text-center">
      <h1 className="text-xl font-semibold text-foreground mb-2">Pro feature</h1>
      <p className="mb-4 text-[14px] text-muted-foreground">The comparison tool requires a Pro subscription.</p>
      <Button asChild><Link to="/pricing">View pricing</Link></Button>
    </div>
  );

  if (error) return (
    <div className="mx-auto max-w-3xl px-4 py-20 text-center">
      <p className="text-[14px] text-muted-foreground">{error}</p>
    </div>
  );

  const rows = [
    { label: 'Score', render: (r: CompareRepo) => <ScoreBadge score={r.reepo_score} size="sm" /> },
    { label: 'Stars', render: (r: CompareRepo) => <span className="font-mono tabular-nums">{formatNumber(r.stars)}</span> },
    { label: 'Forks', render: (r: CompareRepo) => <span className="font-mono tabular-nums">{formatNumber(r.forks)}</span> },
    { label: 'Language', render: (r: CompareRepo) => r.language || '--' },
    { label: 'License', render: (r: CompareRepo) => r.license || '--' },
    { label: 'Issues', render: (r: CompareRepo) => <span className="font-mono tabular-nums">{formatNumber(r.open_issues)}</span> },
    { label: 'Last Push', render: (r: CompareRepo) => r.pushed_at ? new Date(r.pushed_at).toLocaleDateString() : '--' },
    { label: 'Category', render: (r: CompareRepo) => r.category_primary || '--' },
  ];

  const dimensions = ['maintenance_health', 'documentation_quality', 'community_activity', 'popularity', 'freshness', 'license_score'];
  const dimLabels: Record<string, string> = { maintenance_health: 'Maintenance', documentation_quality: 'Docs', community_activity: 'Community', popularity: 'Popularity', freshness: 'Freshness', license_score: 'License' };

  return (
    <div className="mx-auto max-w-4xl animate-fade-in px-4 py-8 sm:px-6">
      <h1 className="mb-6 text-xl font-semibold text-foreground">Compare</h1>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-28"></TableHead>
              {repos.map((r) => (
                <TableHead key={r.id}>
                  <Link to={`/repo/${r.full_name}`} className="hover:underline underline-offset-2">{r.full_name}</Link>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map(({ label, render }) => (
              <TableRow key={label}>
                <TableCell className="font-medium text-muted-foreground">{label}</TableCell>
                {repos.map((r) => <TableCell key={r.id}>{render(r)}</TableCell>)}
              </TableRow>
            ))}
            {dimensions.map((dim) => (
              <TableRow key={dim}>
                <TableCell className="font-medium text-muted-foreground">{dimLabels[dim] || dim}</TableCell>
                {repos.map((r) => {
                  const val = r.score_breakdown?.[dim];
                  return (
                    <TableCell key={r.id} className="font-mono tabular-nums" style={val ? { color: scoreColorVar(val) } : { color: 'var(--fg-subtle)' }}>
                      {val ?? '--'}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
```

**Step 2: Create Stats.tsx**

```tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { StatCard } from '@/components/stat-card';
import { scoreColorVar } from '@/lib/utils';

interface PublicStats {
  total_repos: number;
  repos_by_category: Record<string, number>;
  repos_by_language: Record<string, number>;
  avg_reepo_score: number;
  median_score: number;
  score_distribution: { excellent_80_plus: number; good_60_79: number; fair_40_59: number; poor_below_40: number };
  index_growth: { date: string; total_repos: number }[];
  top_repos_by_score: { full_name: string; reepo_score: number; stars: number; language: string }[];
  newest_repos: { full_name: string; description: string; stars: number; language: string }[];
}

function HorizontalBar({ data, label }: { data: Record<string, number>; label: string }) {
  const entries = Object.entries(data);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <div>
      <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{label}</h3>
      <div className="space-y-1.5">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-center gap-2 text-[13px]">
            <span className="w-20 truncate text-right text-muted-foreground">{key}</span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-foreground/20 transition-all duration-300" style={{ width: `${(value / max) * 100}%` }} />
            </div>
            <span className="w-8 text-right font-mono tabular-nums text-foreground">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DistributionViz({ dist }: { dist: PublicStats['score_distribution'] }) {
  const segments = [
    { label: '80+', value: dist.excellent_80_plus, color: 'var(--score-high)' },
    { label: '60-79', value: dist.good_60_79, color: 'var(--score-mid)' },
    { label: '40-59', value: dist.fair_40_59, color: 'var(--score-mid)' },
    { label: '<40', value: dist.poor_below_40, color: 'var(--score-low)' },
  ];
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;

  return (
    <div>
      <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Score distribution</h3>
      <div className="flex h-2 gap-px overflow-hidden rounded-full">
        {segments.map((s) => (
          <div key={s.label} className="transition-all duration-300" style={{ width: `${(s.value / total) * 100}%`, backgroundColor: s.color }} />
        ))}
      </div>
      <div className="mt-2 flex justify-between">
        {segments.map((s) => (
          <div key={s.label} className="text-center">
            <div className="font-mono text-[15px] font-semibold tabular-nums" style={{ color: s.color }}>{s.value}</div>
            <div className="text-[11px] text-muted-foreground">{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Stats() {
  const [stats, setStats] = useState<PublicStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = 'Stats -- Reepo.dev';
    fetch('/api/public-stats')
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="mx-auto max-w-3xl px-4 py-12"><Skeleton className="h-96" /></div>;
  if (!stats) return <div className="mx-auto max-w-3xl px-4 py-20 text-center text-muted-foreground">Could not load stats</div>;

  return (
    <div className="mx-auto max-w-3xl animate-fade-in px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold text-foreground">Index Stats</h1>
      <p className="mt-1 text-[14px] text-muted-foreground">Open data about the Reepo AI repo index</p>

      <div className="mt-6 grid grid-cols-2 gap-2 md:grid-cols-4">
        <StatCard label="Total Repos" value={stats.total_repos.toLocaleString()} />
        <StatCard label="Avg Score" value={String(stats.avg_reepo_score)} />
        <StatCard label="Median" value={String(stats.median_score)} />
        <StatCard label="Categories" value={String(Object.keys(stats.repos_by_category).length)} />
      </div>

      <Card className="mt-6">
        <CardContent className="p-5">
          <DistributionViz dist={stats.score_distribution} />
        </CardContent>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card><CardContent className="p-5"><HorizontalBar data={stats.repos_by_category} label="By category" /></CardContent></Card>
        <Card><CardContent className="p-5"><HorizontalBar data={stats.repos_by_language} label="Top languages" /></CardContent></Card>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Top by score</h3>
            <div className="space-y-1.5">
              {stats.top_repos_by_score.map((r) => (
                <div key={r.full_name} className="flex items-center justify-between text-[13px]">
                  <Link to={`/repo/${r.full_name}`} className="truncate text-foreground hover:underline underline-offset-2">{r.full_name}</Link>
                  <span className="ml-2 font-mono tabular-nums" style={{ color: scoreColorVar(r.reepo_score) }}>{r.reepo_score}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Recently indexed</h3>
            <div className="space-y-1.5">
              {stats.newest_repos.map((r) => (
                <div key={r.full_name} className="flex items-center justify-between text-[13px]">
                  <Link to={`/repo/${r.full_name}`} className="truncate text-foreground hover:underline underline-offset-2">{r.full_name}</Link>
                  <span className="ml-2 text-muted-foreground">{r.language || '--'}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 text-center">
        <Button variant="outline" size="sm" asChild>
          <a href="/api/open-data/latest.csv">
            <Download className="mr-1.5 h-3 w-3" />
            Download CSV
          </a>
        </Button>
      </div>
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: rebuild Compare and Stats pages"
```

---

### Task 10: Pricing + AdminAnalytics pages

**Files:**
- Delete: `src/pages/Pricing.tsx`, `src/pages/AdminAnalytics.tsx`
- Create: `src/pages/Pricing.tsx`, `src/pages/AdminAnalytics.tsx`

**Step 1: Create Pricing.tsx**

```tsx
import { useEffect, useState } from 'react';
import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface Tier {
  name: string;
  price: string;
  price_yearly?: string;
  features: string[];
}

const FALLBACK_TIERS: Tier[] = [
  {
    name: 'Free',
    price: '$0',
    features: ['Browse all repos', 'Basic search', '3 collections', '100 API requests/day', 'Community access'],
  },
  {
    name: 'Pro',
    price: '$9/mo',
    price_yearly: '$79/yr',
    features: ['Everything in Free', 'Unlimited collections', 'Comparison tool', 'CSV/JSON export', '10,000 API requests/day', 'Priority support'],
  },
];

export default function Pricing() {
  const [tiers, setTiers] = useState<Tier[]>(FALLBACK_TIERS);

  useEffect(() => {
    document.title = 'Pricing -- Reepo.dev';
    fetch('/api/pricing')
      .then((r) => r.json())
      .then((data) => { if (data.tiers) setTiers(data.tiers); })
      .catch(() => {});
  }, []);

  return (
    <div className="mx-auto max-w-2xl animate-fade-in px-4 py-16 sm:px-6">
      <div className="mb-10 text-center">
        <h1 className="text-xl font-semibold text-foreground">Pricing</h1>
        <p className="mt-1 text-[14px] text-muted-foreground">Start free. Upgrade when you need more.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {tiers.map((tier) => (
          <Card key={tier.name} className={tier.name === 'Pro' ? 'ring-1 ring-border' : ''}>
            <CardContent className="flex flex-col p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-[15px] font-semibold text-foreground">{tier.name}</h2>
                {tier.name === 'Pro' && <Badge variant="secondary">Popular</Badge>}
              </div>
              <div className="mb-5 mt-4">
                <span className="font-mono text-3xl font-semibold text-foreground">{tier.price}</span>
                {tier.price_yearly && <span className="ml-1.5 text-[13px] text-muted-foreground">or {tier.price_yearly}</span>}
              </div>
              <ul className="flex-1 space-y-2.5">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-[13px] text-muted-foreground">
                    <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-foreground" />
                    {f}
                  </li>
                ))}
              </ul>
              <Button variant={tier.name === 'Pro' ? 'default' : 'outline'} className="mt-6 w-full">
                {tier.name === 'Pro' ? 'Upgrade to Pro' : 'Current plan'}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Create AdminAnalytics.tsx**

```tsx
import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatCard } from '@/components/stat-card';

interface AnalyticsSummary {
  total_views: number;
  unique_visitors: number;
  top_pages: { path: string; views: number }[];
  top_search_queries: { query: string; count: number; avg_results: number }[];
  top_repos_viewed: { path: string; views: number }[];
  conversion_funnel: { visits: number; searches: number; views: number; saves: number; signups: number; pro_upgrades: number };
  period_days: number;
}

export default function AdminAnalytics() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = 'Analytics -- Reepo.dev';
    setLoading(true);
    fetch(`/api/admin/analytics?days=${days}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) return <div className="mx-auto max-w-3xl px-4 py-12"><Skeleton className="h-96" /></div>;
  if (!data) return <div className="mx-auto max-w-3xl px-4 py-20 text-center text-muted-foreground">Could not load analytics</div>;

  const funnel = data.conversion_funnel;

  return (
    <div className="mx-auto max-w-3xl animate-fade-in px-4 py-8 sm:px-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">Analytics</h1>
        <Tabs value={String(days)} onValueChange={(v) => setDays(Number(v))}>
          <TabsList>
            <TabsTrigger value="7">7d</TabsTrigger>
            <TabsTrigger value="30">30d</TabsTrigger>
            <TabsTrigger value="90">90d</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-2 md:grid-cols-4">
        <StatCard label="Views" value={data.total_views.toLocaleString()} />
        <StatCard label="Visitors" value={data.unique_visitors.toLocaleString()} />
        <StatCard label="Searches" value={funnel.searches.toLocaleString()} />
        <StatCard label="Pro" value={String(funnel.pro_upgrades)} />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Top pages</h3>
            <div className="space-y-1.5">
              {data.top_pages.slice(0, 10).map((p) => (
                <div key={p.path} className="flex items-center justify-between text-[13px]">
                  <span className="truncate text-muted-foreground">{p.path}</span>
                  <span className="ml-2 font-mono tabular-nums text-foreground">{p.views}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Top queries</h3>
            <div className="space-y-1.5">
              {data.top_search_queries.slice(0, 10).map((q) => (
                <div key={q.query} className="flex items-center justify-between text-[13px]">
                  <span className="truncate text-muted-foreground">{q.query}</span>
                  <span className="ml-2 font-mono tabular-nums text-foreground">{q.count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-5">
          <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Funnel</h3>
          <div className="flex h-28 items-end gap-3">
            {Object.entries(funnel).map(([step, value]) => {
              const maxVal = Math.max(...Object.values(funnel), 1);
              const height = Math.max(4, (value / maxVal) * 100);
              return (
                <div key={step} className="flex flex-1 flex-col items-center">
                  <span className="mb-1 font-mono text-[11px] tabular-nums text-foreground">{value}</span>
                  <div className="w-full rounded-sm bg-foreground/15" style={{ height: `${height}%` }} />
                  <span className="mt-1.5 w-full truncate text-center text-[11px] text-muted-foreground">{step}</span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: rebuild Pricing and AdminAnalytics pages"
```

---

### Task 11: Cleanup + verify

**Step 1: Delete any remaining old component files**

```bash
cd /Users/gunnar/Documents/Dev/reepo-dev-platform/frontend
# Remove old-named files if they still exist
rm -f src/components/Layout.tsx src/components/SearchBar.tsx src/components/ScoreBadge.tsx src/components/RepoCard.tsx src/components/CategoryCard.tsx src/components/Pagination.tsx src/components/NewsletterForm.tsx
```

**Step 2: Verify TypeScript compiles**

Run: `npx tsc --noEmit`

Expected: No errors.

**Step 3: Verify dev server starts**

Run: `npm run dev`

Expected: Vite starts on localhost:3000 without errors.

**Step 4: Verify build succeeds**

Run: `npm run build`

Expected: Build completes successfully.

**Step 5: Commit any fixes**

```bash
git add -A
git commit -m "chore: cleanup old files and verify build"
```

---

Plan complete and saved to `docs/plans/2026-03-06-frontend-rebuild.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?