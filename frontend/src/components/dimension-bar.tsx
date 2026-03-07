import { useState } from 'react';
import { Info } from 'lucide-react';
import { scoreColorVar } from '@/lib/utils';

const TOOLTIPS: Record<string, string> = {
  Maintenance: 'Based on how recently the repo was pushed to. Active repos score higher.',
  Documentation: 'Based on README length, wiki presence, and whether a homepage is set.',
  Community: 'Weighted mix of stars, forks, and issue-to-star ratio.',
  Popularity: 'Log-scale measure of stars and forks relative to top repos.',
  Freshness: 'How recently the repo was updated, with a maturity bonus for older repos.',
  License: 'Permissive licenses (MIT, Apache) score highest. No license scores lowest.',
};

interface DimensionCellProps {
  label: string;
  value: number;
  compact?: boolean;
}

export function DimensionCell({ label, value, compact }: DimensionCellProps) {
  const color = scoreColorVar(value);
  const [showTip, setShowTip] = useState(false);
  const tooltip = TOOLTIPS[label];

  if (compact) {
    return (
      <div className="relative flex items-center justify-between py-1.5">
        <span className="flex items-center gap-1 text-[12px] text-muted-foreground">
          {label}
          {tooltip && (
            <button
              className="text-muted-foreground/40 hover:text-muted-foreground transition-colors"
              onMouseEnter={() => setShowTip(true)}
              onMouseLeave={() => setShowTip(false)}
              onClick={() => setShowTip(!showTip)}
            >
              <Info className="h-3 w-3" />
            </button>
          )}
        </span>
        <span
          className="font-mono text-[13px] font-semibold tabular-nums"
          style={{ color }}
        >
          {value}
        </span>
        {showTip && tooltip && (
          <div className="absolute bottom-full left-0 z-10 mb-1 w-48 rounded-md bg-popover p-2 text-[11px] leading-snug text-popover-foreground shadow-md border border-border/50">
            {tooltip}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative rounded-lg border border-border/50 px-3 py-2.5">
      <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
        {label}
        {tooltip && (
          <button
            className="text-muted-foreground/40 hover:text-muted-foreground transition-colors"
            onMouseEnter={() => setShowTip(true)}
            onMouseLeave={() => setShowTip(false)}
            onClick={() => setShowTip(!showTip)}
          >
            <Info className="h-3 w-3" />
          </button>
        )}
      </div>
      <div
        className="mt-0.5 font-mono text-lg font-semibold tabular-nums"
        style={{ color }}
      >
        {value}
      </div>
      {showTip && tooltip && (
        <div className="absolute bottom-full left-0 z-10 mb-1 w-48 rounded-md bg-popover p-2 text-[11px] leading-snug text-popover-foreground shadow-md border border-border/50">
          {tooltip}
        </div>
      )}
    </div>
  );
}
