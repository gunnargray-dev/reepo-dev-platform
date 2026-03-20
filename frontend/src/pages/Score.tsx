import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ScoreCard } from '@/components/score-card';
import type { ScoreResult } from '@/lib/api';
import { scoreRepo } from '@/lib/api';

interface TermLine {
  text: string;
  delay: number;
  color?: string;
  bold?: boolean;
}

const TERM_LINES: TermLine[] = [
  { text: '$ reepo analyze', delay: 0 },
  { text: '', delay: 200 },
  { text: 'Fetching repo metadata...', delay: 400 },
  { text: 'Analyzing maintenance health...', delay: 1000 },
  { text: 'Parsing documentation...', delay: 1600 },
  { text: 'Measuring community activity...', delay: 2100 },
  { text: 'Calculating popularity...', delay: 2500 },
  { text: 'Checking freshness...', delay: 2900 },
  { text: 'Reviewing license...', delay: 3200 },
  { text: '', delay: 3500 },
  { text: 'Computing final score...', delay: 3600 },
];

function TerminalLoading({ repoInput }: { repoInput: string }) {
  const [visibleCount, setVisibleCount] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const lines = TERM_LINES.map((line, i) => {
    if (i === 0) {
      const short = repoInput.replace(/^https?:\/\/(www\.)?github\.com\//, '').replace(/\/$/, '');
      return { ...line, text: `$ reepo analyze ${short}` };
    }
    return line;
  });

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    lines.forEach((line, i) => {
      timers.push(setTimeout(() => setVisibleCount(i + 1), line.delay));
    });
    return () => timers.forEach(clearTimeout);
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [visibleCount]);

  return (
    <div className="mx-auto mt-8 w-full max-w-lg overflow-hidden rounded-lg border border-white/10 bg-[#0d1117] font-mono text-[12px] leading-relaxed animate-fade-in">
      <div className="flex items-center gap-1.5 border-b border-white/10 px-4 py-2">
        <div className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
        <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/80" />
        <div className="h-2.5 w-2.5 rounded-full bg-green-500/80" />
        <span className="ml-2 text-[10px] text-white/30">reepo score</span>
      </div>
      <div ref={containerRef} className="p-4 text-white/70 min-h-[220px]">
        {lines.slice(0, visibleCount).map((line, i) => (
          <div
            key={i}
            style={{
              color: line.color,
              fontWeight: line.bold ? 700 : 400,
              animation: 'fade-in 0.15s ease',
            }}
          >
            {line.text || '\u00A0'}
          </div>
        ))}
        {visibleCount < lines.length && (
          <span className="inline-block w-2 h-4 bg-white/60 animate-pulse" />
        )}
        {visibleCount >= lines.length && (
          <span className="inline-block w-2 h-4 bg-green-400/80 animate-pulse" />
        )}
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
    const minDelay = new Promise((r) => setTimeout(r, 4500));
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

      {/* Terminal loading animation */}
      {loading && <TerminalLoading repoInput={url} />}

      {/* Result card */}
      {result && (
        <div className="mt-6 animate-fade-in">
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
