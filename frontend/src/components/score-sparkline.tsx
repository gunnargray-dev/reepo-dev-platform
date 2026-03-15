interface ScoreSparklineProps {
  data: { score: number }[];
}

export function ScoreSparkline({ data }: ScoreSparklineProps) {
  if (data.length < 2) return null;

  const width = 180;
  const height = 40;
  const padding = 2;

  const scores = data.map((d) => d.score);
  const min = Math.min(...scores);
  const max = Math.max(...scores);
  const range = max - min || 1;

  const points = scores.map((s, i) => {
    const x = padding + (i / (scores.length - 1)) * (width - padding * 2);
    const y = height - padding - ((s - min) / range) * (height - padding * 2);
    return { x, y };
  });

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');
  const areaPath = `${linePath} L${points[points.length - 1].x},${height} L${points[0].x},${height} Z`;

  const delta = scores[scores.length - 1] - scores[0];
  const deltaColor = delta >= 0 ? 'var(--score-high)' : 'var(--score-low)';
  const lineColor = delta >= 0 ? 'var(--score-high)' : 'var(--score-low)';

  const gradientId = 'sparkline-fill';

  return (
    <div className="mt-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] text-muted-foreground">Score trend</span>
        <span className="text-[11px] font-mono tabular-nums" style={{ color: deltaColor }}>
          {delta >= 0 ? '+' : ''}{delta}
        </span>
      </div>
      <svg width={width} height={height} className="w-full" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity="0.15" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill={`url(#${gradientId})`} />
        <path d={linePath} fill="none" stroke={lineColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}
