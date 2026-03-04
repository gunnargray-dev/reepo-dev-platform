import { scoreBgColor } from '../lib/utils';

interface ScoreBadgeProps {
  score: number | null;
  size?: 'sm' | 'md' | 'lg';
}

export default function ScoreBadge({ score, size = 'sm' }: ScoreBadgeProps) {
  const sizeClasses = { sm: 'px-2 py-0.5 text-xs', md: 'px-3 py-1 text-sm', lg: 'px-4 py-2 text-2xl' };

  if (score === null) {
    return <span className={`inline-flex items-center font-mono font-semibold rounded-full bg-gray-700 text-gray-400 ${sizeClasses[size]}`}>—</span>;
  }

  return <span className={`inline-flex items-center font-mono font-semibold rounded-full ${scoreBgColor(score)} ${sizeClasses[size]}`}>{score}</span>;
}
