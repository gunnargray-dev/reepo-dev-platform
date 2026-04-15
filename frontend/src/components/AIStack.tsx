import { Link } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export interface BuildIntent {
  capabilities?: string[];
  constraints?: string[];
  language?: string | null;
  scale?: string | null;
}

export interface StackPick {
  repo_id: number;
  repo: string;
  role: string;
  why: string;
  // Optional repo card fields (populated when backend includes them).
  id?: number;
  owner?: string;
  name?: string;
  description?: string | null;
  stars?: number;
  reepo_score?: number | null;
  language?: string | null;
  topics?: string[];
  category_primary?: string | null;
  license?: string | null;
  updated_at?: string | null;
}

export function StackPickCard({ pick, index = 0 }: { pick: StackPick; index?: number }) {
  const [owner, name] = pick.repo.includes('/') ? pick.repo.split('/') : [null, pick.repo];
  return (
    <div
      className="rounded-xl border border-border/60 bg-background p-5 motion-safe:animate-fade-in"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <Badge variant="secondary" className="text-[11px]">
            {pick.role || 'component'}
          </Badge>
          {owner ? (
            <Link
              to={`/repo/${owner}/${name}`}
              className="text-[15px] font-medium text-foreground hover:underline truncate"
            >
              <span className="text-muted-foreground">{owner}/</span>
              {name}
            </Link>
          ) : (
            <span className="text-[15px] font-medium text-foreground truncate">{pick.repo}</span>
          )}
        </div>
      </div>
      <p className="mt-3 text-[13.5px] leading-relaxed text-foreground/90">{pick.why}</p>
      {(pick.stars !== undefined || pick.language || pick.reepo_score !== undefined) && (
        <div className="mt-3 flex items-center gap-3 text-[12px] text-muted-foreground">
          {pick.stars !== undefined && <span>{pick.stars.toLocaleString()} stars</span>}
          {pick.language && <span>{pick.language}</span>}
          {pick.reepo_score != null && <span>Reepo {Math.round(pick.reepo_score)}</span>}
        </div>
      )}
    </div>
  );
}

export function IntentChips({ intent }: { intent: BuildIntent | null | undefined }) {
  const chips = [
    ...(intent?.capabilities ?? []).map((c) => ({ label: c, kind: 'cap' as const })),
    ...(intent?.constraints ?? []).map((c) => ({ label: c, kind: 'con' as const })),
    ...(intent?.language ? [{ label: intent.language, kind: 'lang' as const }] : []),
  ];
  if (chips.length === 0) return null;
  return (
    <div className="mb-6">
      <div className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
        Intent
      </div>
      <div className="flex flex-wrap gap-1.5">
        {chips.map((c, i) => (
          <Badge
            key={`${c.kind}-${c.label}-${i}`}
            variant={c.kind === 'lang' ? 'outline' : 'secondary'}
            className="text-[11px]"
          >
            {c.label}
          </Badge>
        ))}
      </div>
    </div>
  );
}

export function AIStackResults({
  intent,
  picks,
  degraded,
}: {
  intent: BuildIntent | null | undefined;
  picks: StackPick[];
  degraded?: boolean;
}) {
  return (
    <div>
      <IntentChips intent={intent} />
      {degraded && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-border/60 bg-muted/40 px-3 py-2 text-[12.5px] text-muted-foreground">
          <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>
            Semantic search unavailable — using keyword fallback. Add{' '}
            <code className="rounded bg-muted px-1 py-0.5 text-[11px]">VOYAGE_API_KEY</code> to enable.
          </span>
        </div>
      )}
      {picks.length > 0 && (
        <div>
          <h2 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">
            Stack
          </h2>
          <div className="grid gap-3">
            {picks.map((pick, i) => (
              <StackPickCard key={`${pick.repo_id}-${i}`} pick={pick} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
