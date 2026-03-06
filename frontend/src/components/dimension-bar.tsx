import { scoreColorVar } from '@/lib/utils';

interface DimensionCellProps {
  label: string;
  value: number;
}

export function DimensionCell({ label, value }: DimensionCellProps) {
  const color = scoreColorVar(value);

  return (
    <div className="rounded-lg border border-border px-3 py-2.5">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div
        className="mt-0.5 font-mono text-lg font-semibold tabular-nums"
        style={{ color }}
      >
        {value}
      </div>
    </div>
  );
}
