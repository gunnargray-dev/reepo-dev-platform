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
