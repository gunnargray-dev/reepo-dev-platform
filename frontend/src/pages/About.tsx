import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { scoreColorVar } from '@/lib/utils';

const DIMENSIONS = [
  {
    name: 'Maintenance Health',
    weight: 25,
    key: 'maintenance_health',
    description: 'How actively is the project maintained? Based on how recently code was pushed.',
    details: [
      'Pushed within 30 days: 100',
      'Pushed within 90 days: 70',
      'Pushed within 180 days: 40',
      'Pushed within 1 year: 20',
      'Over 1 year stale: 0',
    ],
  },
  {
    name: 'Community Activity',
    weight: 25,
    key: 'community_activity',
    description: 'How engaged is the community? A weighted blend of stars, forks, and issue health.',
    details: [
      'Star tiers: 10K+ (100), 1K+ (80), 100+ (60), 10+ (40)',
      'Fork tiers: 1K+ (100), 100+ (70), 10+ (40)',
      'Issue ratio (open/stars): lower is healthier',
      'Formula: 50% stars + 30% forks + 20% issue health',
    ],
  },
  {
    name: 'Documentation Quality',
    weight: 15,
    key: 'documentation_quality',
    description: 'Does the project have useful documentation? Based on README length, wiki, and website.',
    details: [
      'README > 2000 chars: 100',
      'README > 500 chars: 70',
      'README > 100 chars: 40',
      'Minimal/no README: 10',
      '+10 bonus for wiki, +10 for homepage',
    ],
  },
  {
    name: 'Popularity',
    weight: 15,
    key: 'popularity',
    description: 'How widely adopted is the project? Logarithmic scale based on stars and forks.',
    details: [
      'Stars scored on log scale (100K = perfect)',
      'Forks scored on log scale (50K = perfect)',
      'Formula: 70% star score + 30% fork score',
    ],
  },
  {
    name: 'Freshness',
    weight: 10,
    key: 'freshness',
    description: 'Is the project actively evolving? Combines recency of updates with project maturity.',
    details: [
      'Pushed within 7 days: 100 recency',
      'Pushed within 30 days: 85 recency',
      'Pushed within 90 days: 60 recency',
      '+30 maturity bonus for projects over 1 year old',
    ],
  },
  {
    name: 'License',
    weight: 10,
    key: 'license_score',
    description: 'How permissive is the license? Permissive licenses score highest for ease of adoption.',
    details: [
      'Permissive (MIT, Apache, BSD): 100',
      'Copyleft (GPL, AGPL, MPL): 70',
      'Other known license: 50',
      'No license specified: 30',
    ],
  },
];

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-muted">
      <div
        className="h-1.5 rounded-full transition-all duration-500"
        style={{ width: `${value}%`, backgroundColor: color }}
      />
    </div>
  );
}

export default function About() {
  useEffect(() => {
    document.title = 'How Reepo Scoring Works -- Reepo.dev';
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      {/* Header */}
      <div className="animate-slide-up">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          How Reepo Scoring Works
        </h1>
        <p className="mt-3 text-[15px] leading-relaxed text-muted-foreground">
          Every repo in our index gets a Reepo Score from 0-100. The score is a weighted composite of six dimensions that measure whether a project is worth depending on — not just whether it's popular.
        </p>
      </div>

      {/* Formula overview */}
      <div className="mt-10 rounded-lg border border-border/60 bg-card p-5">
        <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">The Formula</h2>
        <div className="mt-3 font-mono text-[14px] text-foreground">
          Reepo Score = {DIMENSIONS.map((d, i) => (
            <span key={d.key}>
              {i > 0 && ' + '}
              <span className="text-muted-foreground">{d.weight}%</span>
              {' '}
              <span>{d.name.split(' ')[0]}</span>
            </span>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-6 gap-1.5">
          {DIMENSIONS.map((d) => (
            <div key={d.key} className="text-center">
              <div className="text-[20px] font-bold font-mono tabular-nums text-foreground">{d.weight}%</div>
              <div className="mt-0.5 text-[10px] text-muted-foreground leading-tight">{d.name}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Score interpretation */}
      <div className="mt-10">
        <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">What Scores Mean</h2>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            { range: '80-100', label: 'Excellent', desc: 'Well-maintained, documented, and widely adopted' },
            { range: '60-79', label: 'Good', desc: 'Solid project with some areas to improve' },
            { range: '40-59', label: 'Fair', desc: 'Usable but may have gaps in maintenance or docs' },
            { range: '0-39', label: 'Poor', desc: 'Stale, undocumented, or very early stage' },
          ].map((tier) => {
            const mid = parseInt(tier.range);
            return (
              <div key={tier.range} className="rounded-lg border border-border/60 p-3">
                <div className="font-mono text-lg font-bold tabular-nums" style={{ color: scoreColorVar(mid) }}>
                  {tier.range}
                </div>
                <div className="mt-0.5 text-[13px] font-medium text-foreground">{tier.label}</div>
                <div className="mt-1 text-[11px] text-muted-foreground leading-snug">{tier.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Dimensions detail */}
      <div className="mt-10">
        <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Dimensions in Detail</h2>
        <div className="mt-4 space-y-4">
          {DIMENSIONS.map((dim) => (
            <div key={dim.key} className="rounded-lg border border-border/60 p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-[15px] font-medium text-foreground">{dim.name}</h3>
                <span className="font-mono text-[13px] text-muted-foreground">{dim.weight}% weight</span>
              </div>
              <ScoreBar value={dim.weight * 4} color={scoreColorVar(dim.weight * 4)} />
              <p className="mt-2.5 text-[13px] text-muted-foreground leading-relaxed">{dim.description}</p>
              <ul className="mt-2 space-y-0.5">
                {dim.details.map((detail) => (
                  <li key={detail} className="flex items-start gap-2 text-[12px] text-muted-foreground">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-muted-foreground/40" />
                    <span className="font-mono">{detail}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Philosophy */}
      <div className="mt-10 rounded-lg border border-border/60 bg-card p-5">
        <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Why These Dimensions?</h2>
        <div className="mt-3 space-y-3 text-[14px] leading-relaxed text-muted-foreground">
          <p>
            Stars alone don't tell you if a repo is worth using. A project with 50K stars but no commits in 2 years is a liability, not an asset. Reepo Score weights <strong className="text-foreground">maintenance</strong> and <strong className="text-foreground">community health</strong> equally with popularity because what matters is whether a project will still be around next year.
          </p>
          <p>
            We deliberately weight <strong className="text-foreground">documentation</strong> at 15% — enough to matter, but not enough to penalize fast-moving projects that prioritize code over prose. <strong className="text-foreground">License</strong> and <strong className="text-foreground">freshness</strong> are lower-weight signals that still affect whether you can actually use and depend on a project.
          </p>
          <p>
            Scores are recalculated periodically as repos evolve. A project that goes dormant will see its score drop over time.
          </p>
        </div>
      </div>

      {/* CTA */}
      <div className="mt-10 text-center">
        <p className="text-[14px] text-muted-foreground">
          See it in action —{' '}
          <Link to="/search" className="text-foreground underline underline-offset-2 hover:opacity-70 transition-opacity">
            search repos
          </Link>
          {' '}or{' '}
          <Link to="/trending" className="text-foreground underline underline-offset-2 hover:opacity-70 transition-opacity">
            browse trending
          </Link>.
        </p>
      </div>
    </div>
  );
}
