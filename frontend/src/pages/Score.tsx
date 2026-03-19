import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ScoreCard } from '@/components/score-card';
import type { ScoreResult } from '@/lib/api';
import { scoreRepo } from '@/lib/api';

const SCAN_STEPS = [
  { label: 'Fetching repository', icon: '{}' },
  { label: 'Analyzing maintenance', icon: '//' },
  { label: 'Reading documentation', icon: '##' },
  { label: 'Measuring community', icon: '<>' },
  { label: 'Calculating popularity', icon: '**' },
  { label: 'Checking freshness', icon: '>>' },
  { label: 'Reviewing license', icon: '()' },
  { label: 'Computing score', icon: '::' },
];

function ScanAnimation() {
  const [step, setStep] = useState(0);
  const [dots, setDots] = useState('');

  useEffect(() => {
    const stepInterval = setInterval(() => {
      setStep((s) => (s + 1) % SCAN_STEPS.length);
    }, 1400);
    return () => clearInterval(stepInterval);
  }, []);

  useEffect(() => {
    const dotInterval = setInterval(() => {
      setDots((d) => (d.length >= 3 ? '' : d + '.'));
    }, 400);
    return () => clearInterval(dotInterval);
  }, []);

  return (
    <div className="flex flex-col items-center gap-8 py-16">
      {/* Scanning pulse */}
      <div className="relative h-20 w-20">
        <div className="absolute inset-0 animate-ping rounded-full bg-foreground/5" />
        <div className="absolute inset-2 animate-ping rounded-full bg-foreground/5" style={{ animationDelay: '0.3s' }} />
        <div className="absolute inset-0 flex items-center justify-center rounded-full border border-border bg-card">
          <span
            className="font-mono text-lg text-muted-foreground transition-all duration-300"
            key={step}
          >
            {SCAN_STEPS[step].icon}
          </span>
        </div>
      </div>

      {/* Step label */}
      <div className="flex flex-col items-center gap-2">
        <span
          className="text-[14px] font-medium text-foreground transition-all duration-300"
          key={`label-${step}`}
          style={{ animation: 'fade-in 0.3s ease' }}
        >
          {SCAN_STEPS[step].label}{dots}
        </span>

        {/* Step indicators */}
        <div className="flex items-center gap-1.5 mt-2">
          {SCAN_STEPS.map((_, i) => (
            <div
              key={i}
              className="h-1 rounded-full transition-all duration-500"
              style={{
                width: i === step ? 16 : 4,
                backgroundColor: i <= step ? 'var(--fg)' : 'var(--border)',
                opacity: i <= step ? 1 : 0.4,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Score() {
  const [searchParams] = useSearchParams();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<ScoreResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const repo = searchParams.get('repo');
    if (repo) {
      setUrl(repo);
      runScore(repo);
    } else {
      inputRef.current?.focus();
    }
  }, []);

  const runScore = async (input: string) => {
    if (!input.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    const minDelay = new Promise((r) => setTimeout(r, 4000));
    try {
      const [data] = await Promise.all([scoreRepo(input.trim()), minDelay]);
      setResult(data);
      document.title = `${data.repo.full_name} — Reepo Score ${data.reepo_score}`;
    } catch (err: any) {
      await minDelay;
      setError(err.message || 'Failed to score repo');
    } finally {
      setLoading(false);
    }
  };

  const handleScore = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    runScore(url);
  };

  const handleScoreAnother = () => {
    setResult(null);
    setUrl('');
    document.title = 'Reepo Score';
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      {/* Header — hide when showing result */}
      {!result && !loading && (
        <div className="text-center animate-fade-in">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            Get your Reepo Score
          </h1>
          <p className="mt-2 text-[14px] text-muted-foreground">
            Paste any GitHub repo to see how it scores on maintenance, docs, community, and more.
          </p>
        </div>
      )}

      {/* Input form — hide during loading and result */}
      {!loading && !result && (
        <form onSubmit={handleScore} className="mt-8 flex gap-2 animate-fade-in">
          <input
            ref={inputRef}
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="github.com/owner/repo or owner/repo"
            className="h-11 flex-1 rounded-lg border border-border bg-background px-4 text-[14px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/30"
          />
          <Button type="submit" disabled={!url.trim()} className="h-11 px-6">
            Score
          </Button>
        </form>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="mt-6 text-center animate-fade-in">
          <p className="text-[13px] text-red-500">{error}</p>
          <Button variant="ghost" size="sm" className="mt-3" onClick={handleScoreAnother}>
            Try another
          </Button>
        </div>
      )}

      {/* Loading animation */}
      {loading && <ScanAnimation />}

      {/* Result card */}
      {result && (
        <div className="mt-6">
          <ScoreCard result={result} />
          <div className="mt-6 text-center">
            <Button variant="ghost" size="sm" className="text-[13px] text-muted-foreground" onClick={handleScoreAnother}>
              Score another repo
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
