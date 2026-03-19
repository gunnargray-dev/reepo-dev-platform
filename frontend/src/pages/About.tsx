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
      ['Pushed within 30 days', '100'],
      ['Pushed within 90 days', '70'],
      ['Pushed within 180 days', '40'],
      ['Pushed within 1 year', '20'],
      ['Over 1 year stale', '0'],
    ],
  },
  {
    name: 'Community Activity',
    weight: 25,
    key: 'community_activity',
    description: 'How engaged is the community? A weighted blend of stars, forks, and issue health.',
    details: [
      ['Star tiers', '10K+=100, 1K+=80, 100+=60'],
      ['Fork tiers', '1K+=100, 100+=70, 10+=40'],
      ['Issue ratio (open/stars)', 'Lower is healthier'],
      ['Formula', '50% stars + 30% forks + 20% issues'],
    ],
  },
  {
    name: 'Documentation Quality',
    weight: 15,
    key: 'documentation_quality',
    description: 'Does the project have useful documentation? Based on README length, wiki, and website.',
    details: [
      ['README > 2000 chars', '100'],
      ['README > 500 chars', '70'],
      ['README > 100 chars', '40'],
      ['Minimal/no README', '10'],
      ['Wiki or homepage bonus', '+10 each'],
    ],
  },
  {
    name: 'Popularity',
    weight: 15,
    key: 'popularity',
    description: 'How widely adopted is the project? Logarithmic scale based on stars and forks.',
    details: [
      ['Stars scored on log scale', '100K = perfect'],
      ['Forks scored on log scale', '50K = perfect'],
      ['Formula', '70% stars + 30% forks'],
    ],
  },
  {
    name: 'Freshness',
    weight: 10,
    key: 'freshness',
    description: 'Is the project actively evolving? Combines recency of updates with project maturity.',
    details: [
      ['Pushed within 7 days', '100 recency'],
      ['Pushed within 30 days', '85 recency'],
      ['Pushed within 90 days', '60 recency'],
      ['Maturity bonus', '+30 for projects > 1 year'],
    ],
  },
  {
    name: 'License',
    weight: 10,
    key: 'license_score',
    description: 'How permissive is the license? Permissive licenses score highest for ease of adoption.',
    details: [
      ['MIT, Apache, BSD', '100'],
      ['GPL, AGPL, MPL', '70'],
      ['Other known license', '50'],
      ['No license specified', '30'],
    ],
  },
];

const TIERS = [
  { range: '80-100', label: 'Excellent', desc: 'Well-maintained, documented, and widely adopted', mid: 90 },
  { range: '60-79', label: 'Good', desc: 'Solid project with some areas to improve', mid: 70 },
  { range: '40-59', label: 'Fair', desc: 'Usable but may have gaps in maintenance or docs', mid: 50 },
  { range: '0-39', label: 'Poor', desc: 'Stale, undocumented, or very early stage', mid: 20 },
];

export default function About() {
  useEffect(() => {
    document.title = 'How Reepo Scoring Works -- Reepo.dev';
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
      {/* Hero */}
      <div className="animate-slide-up text-center">
        <p className="text-[12px] font-medium uppercase tracking-[0.2em] text-muted-foreground">Methodology</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          How Reepo Scoring Works
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-[15px] leading-relaxed text-muted-foreground">
          Every repo gets a score from 0-100. Six dimensions measure whether a project is worth depending on — not just whether it's popular.
        </p>
      </div>

      {/* Formula — visual weight breakdown */}
      <div className="mt-16 animate-slide-up" style={{ animationDelay: '60ms' }}>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">The Formula</h2>
          <div className="flex-1 h-px bg-border" />
        </div>

        {/* Weight bar visualization */}
        <div className="flex h-3 w-full overflow-hidden rounded-full">
          {DIMENSIONS.map((d, i) => {
            const colors = [
              'bg-emerald-500 dark:bg-emerald-400',
              'bg-blue-500 dark:bg-blue-400',
              'bg-violet-500 dark:bg-violet-400',
              'bg-amber-500 dark:bg-amber-400',
              'bg-rose-400 dark:bg-rose-400',
              'bg-slate-400 dark:bg-slate-500',
            ];
            return (
              <div
                key={d.key}
                className={`${colors[i]} ${i > 0 ? 'border-l-2 border-background' : ''}`}
                style={{ width: `${d.weight}%` }}
              />
            );
          })}
        </div>

        {/* Weight labels */}
        <div className="mt-3 flex">
          {DIMENSIONS.map((d, i) => {
            const colors = [
              'text-emerald-600 dark:text-emerald-400',
              'text-blue-600 dark:text-blue-400',
              'text-violet-600 dark:text-violet-400',
              'text-amber-600 dark:text-amber-400',
              'text-rose-500 dark:text-rose-400',
              'text-slate-500 dark:text-slate-400',
            ];
            return (
              <div key={d.key} className="text-center" style={{ width: `${d.weight}%` }}>
                <div className={`text-[13px] font-bold font-mono tabular-nums ${colors[i]}`}>{d.weight}%</div>
                <div className="text-[10px] text-muted-foreground leading-tight mt-0.5">
                  {d.name.split(' ')[0]}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Score tiers */}
      <div className="mt-16 animate-slide-up" style={{ animationDelay: '120ms' }}>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Score Interpretation</h2>
          <div className="flex-1 h-px bg-border" />
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {TIERS.map((tier) => {
            const color = scoreColorVar(tier.mid);
            return (
              <div
                key={tier.range}
                className="relative overflow-hidden rounded-lg border border-border/60 p-4"
              >
                <div
                  className="absolute inset-0 opacity-[0.04]"
                  style={{ backgroundColor: color }}
                />
                <div className="relative">
                  <div className="font-mono text-2xl font-bold tabular-nums" style={{ color }}>
                    {tier.range}
                  </div>
                  <div className="mt-1 text-[13px] font-medium text-foreground">{tier.label}</div>
                  <div className="mt-1.5 text-[11px] text-muted-foreground leading-snug">{tier.desc}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Dimensions detail */}
      <div className="mt-16 animate-slide-up" style={{ animationDelay: '180ms' }}>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Dimensions in Detail</h2>
          <div className="flex-1 h-px bg-border" />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {DIMENSIONS.map((dim, i) => {
            const colors = [
              'border-l-emerald-500 dark:border-l-emerald-400',
              'border-l-blue-500 dark:border-l-blue-400',
              'border-l-violet-500 dark:border-l-violet-400',
              'border-l-amber-500 dark:border-l-amber-400',
              'border-l-rose-400 dark:border-l-rose-400',
              'border-l-slate-400 dark:border-l-slate-500',
            ];
            return (
              <div
                key={dim.key}
                className={`rounded-lg border border-border/60 border-l-2 ${colors[i]} p-4`}
              >
                <div className="flex items-baseline justify-between gap-2">
                  <h3 className="text-[15px] font-medium text-foreground">{dim.name}</h3>
                  <span className="shrink-0 font-mono text-[12px] font-bold text-muted-foreground">{dim.weight}%</span>
                </div>
                <p className="mt-2 text-[13px] text-muted-foreground leading-relaxed">{dim.description}</p>

                <div className="mt-3 space-y-1">
                  {dim.details.map(([label, value]) => (
                    <div key={label} className="flex items-baseline justify-between gap-2 text-[12px]">
                      <span className="text-muted-foreground">{label}</span>
                      <span className="shrink-0 font-mono text-foreground/70">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* New repo adjustment */}
      <div className="mt-16 animate-slide-up" style={{ animationDelay: '240ms' }}>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">New Repo Adjustment</h2>
          <div className="flex-1 h-px bg-border" />
        </div>

        <div className="space-y-4 text-[14px] leading-relaxed text-muted-foreground">
          <p>
            Brand new repos shouldn't be penalized for not having stars yet. For repos less than <strong className="text-foreground">90 days old</strong>, we adjust the dimension weights so that community and popularity carry less influence, while maintenance, documentation, and freshness carry more.
          </p>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-border/60 p-4">
            <div className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground mb-3">New repos (&lt; 90 days)</div>
            <div className="space-y-1.5">
              {[
                ['Maintenance', '30%'],
                ['Documentation', '25%'],
                ['Freshness', '15%'],
                ['Community', '10%'],
                ['Popularity', '10%'],
                ['License', '10%'],
              ].map(([label, value]) => (
                <div key={label} className="flex items-baseline justify-between text-[12px]">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-mono text-foreground/70">{value}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-lg border border-border/60 p-4">
            <div className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground mb-3">Mature repos (90+ days)</div>
            <div className="space-y-1.5">
              {[
                ['Maintenance', '25%'],
                ['Community', '25%'],
                ['Documentation', '15%'],
                ['Popularity', '15%'],
                ['Freshness', '10%'],
                ['License', '10%'],
              ].map(([label, value]) => (
                <div key={label} className="flex items-baseline justify-between text-[12px]">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-mono text-foreground/70">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <p className="mt-4 text-[13px] text-muted-foreground">
          The transition is gradual — weights blend linearly over the first 90 days, so there's no sudden jump.
        </p>
      </div>

      {/* Rescoring cadence */}
      <div className="mt-16 animate-slide-up" style={{ animationDelay: '300ms' }}>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">How Often Scores Update</h2>
          <div className="flex-1 h-px bg-border" />
        </div>

        <div className="space-y-4 text-[14px] leading-relaxed text-muted-foreground">
          <p>
            Scores are <strong className="text-foreground">recalculated weekly</strong>. Every 7 days we re-fetch repo metadata from GitHub and re-run the scoring algorithm. This means a repo that goes dormant will see its maintenance and freshness scores drop over time, while a repo that picks up momentum will climb.
          </p>
          <p>
            Star velocity — how fast a repo is gaining stars — is tracked daily for trending repos. New repos are discovered and scored within 24 hours of being indexed.
          </p>
        </div>
      </div>

      {/* Philosophy */}
      <div className="mt-16 animate-slide-up" style={{ animationDelay: '360ms' }}>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Philosophy</h2>
          <div className="flex-1 h-px bg-border" />
        </div>

        <div className="space-y-4 text-[14px] leading-relaxed text-muted-foreground">
          <p>
            Stars alone don't tell you if a repo is worth using. A project with 50K stars but no commits in 2 years is a liability, not an asset. Reepo Score weights <strong className="text-foreground">maintenance</strong> and <strong className="text-foreground">community health</strong> equally with popularity because what matters is whether a project will still be around next year.
          </p>
          <p>
            We deliberately weight <strong className="text-foreground">documentation</strong> at 15% — enough to matter, but not enough to penalize fast-moving projects that prioritize code over prose. <strong className="text-foreground">License</strong> and <strong className="text-foreground">freshness</strong> are lower-weight signals that still affect whether you can actually use and depend on a project.
          </p>
        </div>
      </div>

      {/* CTA */}
      <div className="mt-16 text-center animate-slide-up" style={{ animationDelay: '420ms' }}>
        <div className="mx-auto h-px w-24 bg-gradient-to-r from-transparent via-border to-transparent mb-8" />
        <p className="text-[14px] text-muted-foreground">
          See it in action —{' '}
          <Link to="/score" className="text-foreground underline underline-offset-2 hover:opacity-70 transition-opacity">
            score a repo
          </Link>
          ,{' '}
          <Link to="/search" className="text-foreground underline underline-offset-2 hover:opacity-70 transition-opacity">
            search repos
          </Link>
          , or{' '}
          <Link to="/trending" className="text-foreground underline underline-offset-2 hover:opacity-70 transition-opacity">
            browse trending
          </Link>.
        </p>
      </div>
    </div>
  );
}
