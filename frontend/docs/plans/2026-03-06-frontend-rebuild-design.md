# Reepo.dev Frontend Rebuild

## Stack
- React 18 + Vite + Tailwind v4 + shadcn/ui
- Geist + Geist Mono fonts
- react-router-dom v6 (existing routing unchanged)
- next-themes for light/dark mode
- All existing API fetchers and types in lib/api.ts unchanged

## Color System
Monochromatic grayscale, single understated accent (blue-gray). Light mode default.
- 3 foreground tiers: primary, muted, subtle
- Score colors (green/amber/red) applied via inline styles, only for score indicators
- Borders: 1px, low-opacity

## Layout
- Sticky frosted-glass header: logo left, nav center, search + theme toggle right
- Command-K search dialog (shadcn CommandDialog) replaces header search input
- Max-width: max-w-5xl
- Clean minimal footer
- Page fade-in animations

## shadcn Components Used
Button, Badge, Card, Input, Select, Slider, Table, Tabs, Separator, Skeleton, Dialog, Command, DropdownMenu, Toggle

## Custom Components
ScoreBadge, RepoCard, DimensionBar, StatCard, CategoryCard

## Pages

### Home
Large heading hero, command-K trigger button, inline stats, category card grid, trending repo cards.

### Search
Left sidebar filters (Select, RadioGroup, Slider). RepoCard list. Pagination.

### RepoDetail
Owner avatar + repo name. Meta row (stars, forks, language, license). Score: bold large number + 6 dimension bars in grid. Topics as Badges. Similar repos below.

### Category
Title + description, repo list with pagination.

### Trending
Tabs for day/week/month. Numbered repo cards with star deltas.

### Compare
shadcn Table with score badges inline.

### Stats
StatCard grid. Segmented score distribution bar. Horizontal bar charts for categories/languages. Compact top/newest repo lists.

### Pricing
Two-column Card layout with feature checklists. Pro card with ring highlight.

### AdminAnalytics
Tabs for time period. Stat cards. Compact tables for top pages/queries. Funnel bar chart.

## What Stays
- lib/api.ts (all fetchers and types)
- lib/utils.ts (formatNumber, timeAgo, languageColor; score helpers updated)
- Route structure in App.tsx

## What Gets Deleted
- All current component and page .tsx files (rebuilt)
- index.css (replaced by shadcn globals.css)
- tailwind.config.ts (replaced by Tailwind v4 CSS config)
- theme.tsx (replaced by next-themes)
- postcss.config.js (Tailwind v4 uses Vite plugin)
