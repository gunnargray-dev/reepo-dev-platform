import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, GitFork, Copy, Check, ExternalLink, Github } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { scoreColorVar, formatNumber } from '@/lib/utils';
import type { ScoreResult } from '@/lib/api';

const DIMENSIONS: { key: string; label: string }[] = [
  { key: 'maintenance_health', label: 'Maintenance' },
  { key: 'documentation_quality', label: 'Docs' },
  { key: 'community_activity', label: 'Community' },
  { key: 'popularity', label: 'Popularity' },
  { key: 'freshness', label: 'Freshness' },
  { key: 'license_score', label: 'License' },
];

function ScoreRing({ score, size = 160 }: { score: number; size?: number }) {
  const strokeWidth = 6;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const [offset, setOffset] = useState(circumference);
  const color = scoreColorVar(score);

  useEffect(() => {
    const timer = setTimeout(() => {
      setOffset(circumference - (score / 100) * circumference);
    }, 100);
    return () => clearTimeout(timer);
  }, [score, circumference]);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="rotate-[-90deg]">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <AnimatedScore value={score} color={color} />
        <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground mt-0.5">
          Score
        </span>
      </div>
    </div>
  );
}

function AnimatedScore({ value, color }: { value: number; color: string }) {
  const [display, setDisplay] = useState(0);
  const frameRef = useRef(0);

  useEffect(() => {
    const start = performance.now();
    const duration = 1200;
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(value * eased));
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value]);

  return (
    <span
      className="font-mono text-4xl font-bold tabular-nums leading-none"
      style={{ color }}
    >
      {display}
    </span>
  );
}

function DimensionBar({ label, value, delay }: { label: string; value: number; delay: number }) {
  const [width, setWidth] = useState(0);
  const color = scoreColorVar(value);

  useEffect(() => {
    const timer = setTimeout(() => setWidth(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return (
    <div className="group">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] text-muted-foreground">{label}</span>
        <span
          className="font-mono text-[12px] font-semibold tabular-nums"
          style={{ color }}
        >
          {value}
        </span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-border/50 overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{
            width: `${width}%`,
            backgroundColor: color,
            transition: 'width 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        />
      </div>
    </div>
  );
}

interface ScoreCardProps {
  result: ScoreResult;
}

export function ScoreCard({ result }: ScoreCardProps) {
  const [copied, setCopied] = useState(false);
  const [entered, setEntered] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [mousePos, setMousePos] = useState({ px: 50, py: 50 });
  const [hovering, setHovering] = useState(false);

  const shareUrl = `${window.location.origin}/score?repo=${encodeURIComponent(result.repo.full_name)}`;

  useEffect(() => {
    const timer = setTimeout(() => setEntered(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setTilt({
      x: (y - 0.5) * -8,
      y: (x - 0.5) * 8,
    });
    setMousePos({ px: x * 100, py: y * 100 });
  };

  const handleMouseEnter = () => setHovering(true);
  const handleMouseLeave = () => {
    setHovering(false);
    setTilt({ x: 0, y: 0 });
  };

  return (
    <div
      className="perspective-[1200px] mx-auto w-full max-w-md"
      style={{
        opacity: entered ? 1 : 0,
        transform: entered ? 'translateY(0)' : 'translateY(20px)',
        transition: 'opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1), transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
      }}
    >
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="relative rounded-2xl bg-card overflow-hidden"
        style={{
          transform: `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
          transition: hovering
            ? 'transform 0.1s ease-out'
            : 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
          transformStyle: 'preserve-3d',
          border: '1px solid transparent',
          backgroundClip: 'padding-box',
        }}
      >
        {/* Edge highlight — radial glow on the border that follows cursor */}
        <div
          className="pointer-events-none absolute -inset-px rounded-2xl transition-opacity duration-300"
          style={{
            opacity: hovering ? 1 : 0,
            background: `radial-gradient(circle at ${mousePos.px}% ${mousePos.py}%, rgba(255,255,255,0.6), rgba(255,255,255,0.12) 40%, var(--border) 70%)`,
            zIndex: -1,
          }}
        />
        {/* Default border (visible when not hovering) */}
        <div
          className="pointer-events-none absolute -inset-px rounded-2xl transition-opacity duration-300"
          style={{
            opacity: hovering ? 0 : 1,
            background: 'var(--border)',
            zIndex: -1,
          }}
        />
        {/* Inner bg to mask the border layers */}
        <div className="absolute inset-px rounded-[15px] bg-card" style={{ zIndex: -1 }} />

        {/* Shimmer overlay on hover */}
        <div
          className="pointer-events-none absolute inset-0 z-10 transition-opacity duration-300"
          style={{
            opacity: hovering ? 0.06 : 0,
            background: `radial-gradient(circle at ${mousePos.px}% ${mousePos.py}%, white, transparent 60%)`,
          }}
        />

        {/* Card content */}
        <div className="relative z-0 px-6 pt-6 pb-5">
          {/* Header: repo info + score ring */}
          <div className="flex items-start gap-5">
            <div className="flex-1 min-w-0 pt-2">
              <Link
                to={`/repo/${result.repo.owner}/${result.repo.name}`}
                className="text-lg font-semibold text-foreground hover:underline underline-offset-2 leading-tight"
              >
                <span className="text-muted-foreground font-normal">{result.repo.owner}/</span>
                {result.repo.name}
              </Link>
              {result.repo.description && (
                <p className="mt-1.5 text-[12px] text-muted-foreground line-clamp-2 leading-relaxed">
                  {result.repo.description}
                </p>
              )}
              <div className="mt-3 flex items-center gap-3 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Star className="h-3 w-3" />
                  {formatNumber(result.repo.stars)}
                </span>
                <span className="flex items-center gap-1">
                  <GitFork className="h-3 w-3" />
                  {formatNumber(result.repo.forks)}
                </span>
                {result.repo.language && (
                  <span className="rounded-full bg-muted px-2 py-0.5 text-[10px]">
                    {result.repo.language}
                  </span>
                )}
              </div>
            </div>

            <div className="flex-shrink-0">
              <ScoreRing score={result.reepo_score} size={100} />
            </div>
          </div>

          {/* Divider */}
          <div className="my-5 h-px bg-border/60" />

          {/* Dimension bars */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-3">
            {DIMENSIONS.map(({ key, label }, i) => (
              <DimensionBar
                key={key}
                label={label}
                value={result.score_breakdown[key as keyof typeof result.score_breakdown]}
                delay={200 + i * 100}
              />
            ))}
          </div>

        </div>

        {/* Footer: branding left, action icons right */}
        <div className="flex items-center justify-between border-t border-border/60 bg-muted/30 px-6 py-3">
          <div className="flex items-center gap-1.5">
            <img src="/reepo-logo.svg" alt="Reepo" className="h-2.5 invert dark:invert-0" />
            <span className="text-[10px] text-muted-foreground/60 font-medium">score</span>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground" onClick={handleCopy} title={copied ? 'Copied!' : 'Copy link'}>
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground" asChild title="View on GitHub">
              <a href={result.repo.url} target="_blank" rel="noopener noreferrer">
                <Github className="h-3.5 w-3.5" />
              </a>
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground" asChild title="View details">
              <Link to={`/repo/${result.repo.owner}/${result.repo.name}`}>
                <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
