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

export function scoreColor(score: number | null): string {
  if (score === null) return 'text-gray-500';
  if (score >= 80) return 'text-score-green';
  if (score >= 50) return 'text-score-yellow';
  return 'text-score-red';
}

export function scoreBgColor(score: number | null): string {
  if (score === null) return 'bg-gray-800 text-gray-500';
  if (score >= 80) return 'bg-score-green/15 text-score-green';
  if (score >= 50) return 'bg-score-yellow/15 text-score-yellow';
  return 'bg-score-red/15 text-score-red';
}

const LANGUAGE_COLORS: Record<string, string> = {
  Python: '#3572A5',
  JavaScript: '#f1e05a',
  TypeScript: '#3178c6',
  Rust: '#dea584',
  Go: '#00ADD8',
  'C++': '#f34b7d',
  C: '#555555',
  Java: '#b07219',
  'C#': '#178600',
  Ruby: '#701516',
  Swift: '#F05138',
  Kotlin: '#A97BFF',
  Jupyter: '#DA5B0B',
  Scala: '#c22d40',
  R: '#198CE7',
  Lua: '#000080',
  Shell: '#89e051',
};

export function languageColor(lang: string | null): string {
  if (!lang) return '#6b7280';
  return LANGUAGE_COLORS[lang] || '#6b7280';
}

const CATEGORY_EMOJI: Record<string, string> = {
  frameworks: '🏗️',
  'apis-sdks': '🔌',
  agents: '🤖',
  apps: '📱',
  'tools-utilities': '🔧',
  models: '🧠',
  datasets: '📊',
  infrastructure: '⚙️',
  'skills-plugins': '🧩',
  libraries: '📚',
};

export function categoryIcon(slug: string): string {
  return CATEGORY_EMOJI[slug] || '📦';
}
