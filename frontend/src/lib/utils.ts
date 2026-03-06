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
