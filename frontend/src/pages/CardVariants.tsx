import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, GitFork, Copy, Check, ExternalLink, Github } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { scoreColorVar, formatNumber } from '@/lib/utils';
import type { ScoreResult, ScoreBreakdown } from '@/lib/api';

/* ═══════════════════════════════════════════════
   Mock Data
   ═══════════════════════════════════════════════ */

const MOCK: ScoreResult = {
  repo: {
    owner: 'anthropics',
    name: 'skills',
    full_name: 'anthropics/skills',
    description: 'Public repository for Agent Skills — extensible capabilities for Claude.',
    url: 'https://github.com/anthropics/skills',
    stars: 97537,
    forks: 10548,
    language: 'Python',
    license: 'MIT',
    category: 'agents',
  },
  reepo_score: 78,
  score_breakdown: {
    maintenance_health: 100,
    documentation_quality: 45,
    community_activity: 98,
    popularity: 96,
    freshness: 100,
    license_score: 30,
  },
};

const DIMENSIONS: { key: string; label: string }[] = [
  { key: 'maintenance_health', label: 'Maintenance' },
  { key: 'documentation_quality', label: 'Docs' },
  { key: 'community_activity', label: 'Community' },
  { key: 'popularity', label: 'Popularity' },
  { key: 'freshness', label: 'Freshness' },
  { key: 'license_score', label: 'License' },
];

/* ═══════════════════════════════════════════════
   Shared Card Internals (same layout every time)
   ═══════════════════════════════════════════════ */

function ScoreRing({ score, size = 120 }: { score: number; size?: number }) {
  const sw = 6;
  const r = (size - sw) / 2;
  const circ = 2 * Math.PI * r;
  const color = scoreColorVar(score);
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="rotate-[-90deg]">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--border)" strokeWidth={sw} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={circ - (score/100)*circ} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-5xl font-bold tabular-nums leading-none" style={{ color }}>{score}</span>
        <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground mt-0.5">Score</span>
      </div>
    </div>
  );
}

function CardContent({ result }: { result: ScoreResult }) {
  return (
    <>
      <div className="relative z-0 px-6 pt-6 pb-5">
        <div className="flex items-start gap-5">
          <div className="flex-1 min-w-0 pt-2">
            <div className="text-lg font-semibold text-foreground leading-tight">
              <span className="text-muted-foreground font-normal">{result.repo.owner}/</span>
              {result.repo.name}
            </div>
            {result.repo.description && (
              <p className="mt-1.5 text-[12px] text-muted-foreground line-clamp-2 leading-relaxed">{result.repo.description}</p>
            )}
            <div className="mt-3 flex items-center gap-3 text-[11px] text-muted-foreground">
              <span className="flex items-center gap-1"><Star className="h-3 w-3" />{formatNumber(result.repo.stars)}</span>
              <span className="flex items-center gap-1"><GitFork className="h-3 w-3" />{formatNumber(result.repo.forks)}</span>
              {result.repo.language && <span className="rounded-full bg-muted px-2 py-0.5 text-[10px]">{result.repo.language}</span>}
            </div>
          </div>
          <div className="flex-shrink-0"><ScoreRing score={result.reepo_score} /></div>
        </div>
        <div className="my-5 h-px bg-border/60" />
        <div className="grid grid-cols-2 gap-x-6 gap-y-3">
          {DIMENSIONS.map(({ key, label }) => {
            const v = result.score_breakdown[key as keyof ScoreBreakdown];
            const color = scoreColorVar(v);
            return (
              <div key={key}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] text-muted-foreground">{label}</span>
                  <span className="font-mono text-[12px] font-semibold tabular-nums" style={{ color }}>{v}</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-border/50 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${v}%`, backgroundColor: color }} />
                </div>
              </div>
            );
          })}
        </div>
        <div className="mt-5 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <img src="/reepo-logo.svg" alt="Reepo" className="h-2.5 invert dark:invert-0" />
            <span className="text-[10px] text-muted-foreground/60 font-medium">score</span>
          </div>
          {result.repo.category && <span className="text-[10px] text-muted-foreground/60">{result.repo.category}</span>}
        </div>
      </div>
      <div className="flex items-center justify-center gap-2 border-t border-border/60 bg-muted/30 px-6 py-3">
        <Button variant="ghost" size="sm" className="h-8 text-[12px]"><Copy className="mr-1.5 h-3 w-3" />Share</Button>
        <Button variant="ghost" size="sm" className="h-8 text-[12px]"><Github className="mr-1.5 h-3 w-3" />GitHub</Button>
        <Button variant="ghost" size="sm" className="h-8 text-[12px]">View details</Button>
      </div>
    </>
  );
}

/* ═══════════════════════════════════════════════
   Variant Shell — wraps CardContent with an effect
   ═══════════════════════════════════════════════ */

interface ShellProps {
  title: string;
  overlay: (hovering: boolean, mx: number, my: number) => React.ReactNode;
  result: ScoreResult;
  tiltStrength?: number;
}

function VariantShell({ title, overlay, result, tiltStrength = 8 }: ShellProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [mouse, setMouse] = useState({ px: 50, py: 50, x: 0, y: 0 });
  const [hovering, setHovering] = useState(false);

  const onMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const nx = (e.clientX - r.left) / r.width;
    const ny = (e.clientY - r.top) / r.height;
    setTilt({ x: (ny - 0.5) * -tiltStrength, y: (nx - 0.5) * tiltStrength });
    setMouse({ px: nx * 100, py: ny * 100, x: e.clientX - r.left, y: e.clientY - r.top });
  };

  return (
    <div>
      <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{title}</h3>
      <div className="perspective-[1200px] mx-auto w-full max-w-md">
        <div
          ref={ref}
          onMouseMove={onMove}
          onMouseEnter={() => setHovering(true)}
          onMouseLeave={() => { setHovering(false); setTilt({ x: 0, y: 0 }); }}
          className="relative rounded-2xl border border-border/80 bg-card overflow-hidden"
          style={{
            transform: `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
            transition: hovering ? 'transform 0.1s ease-out' : 'transform 0.4s cubic-bezier(0.16,1,0.3,1)',
            transformStyle: 'preserve-3d',
          }}
        >
          {overlay(hovering, mouse.px, mouse.py)}
          <CardContent result={result} />
        </div>
      </div>
    </div>
  );
}

/* Canvas shell for canvas-based overlays */
interface CanvasShellProps {
  title: string;
  draw: (ctx: CanvasRenderingContext2D, w: number, h: number, mx: number, my: number, hovering: boolean) => void;
  result: ScoreResult;
}

function CanvasShell({ title, draw, result }: CanvasShellProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [mouse, setMouse] = useState({ x: 0, y: 0, px: 50, py: 50 });
  const [hovering, setHovering] = useState(false);
  const frameRef = useRef(0);

  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
      canvas.width = w * dpr;
      canvas.height = h * dpr;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    draw(ctx, w, h, mouse.x, mouse.y, hovering);
  }, [draw, mouse, hovering]);

  useEffect(() => {
    let running = true;
    const loop = () => {
      if (!running) return;
      render();
      frameRef.current = requestAnimationFrame(loop);
    };
    loop();
    return () => { running = false; cancelAnimationFrame(frameRef.current); };
  }, [render]);

  const onMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const r = cardRef.current.getBoundingClientRect();
    const nx = (e.clientX - r.left) / r.width;
    const ny = (e.clientY - r.top) / r.height;
    setTilt({ x: (ny - 0.5) * -8, y: (nx - 0.5) * 8 });
    setMouse({ x: e.clientX - r.left, y: e.clientY - r.top, px: nx * 100, py: ny * 100 });
  };

  return (
    <div>
      <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{title}</h3>
      <div className="perspective-[1200px] mx-auto w-full max-w-md">
        <div
          ref={cardRef}
          onMouseMove={onMove}
          onMouseEnter={() => setHovering(true)}
          onMouseLeave={() => { setHovering(false); setTilt({ x: 0, y: 0 }); }}
          className="relative rounded-2xl border border-border/80 bg-card overflow-hidden"
          style={{
            transform: `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
            transition: hovering ? 'transform 0.1s ease-out' : 'transform 0.4s cubic-bezier(0.16,1,0.3,1)',
            transformStyle: 'preserve-3d',
          }}
        >
          <canvas ref={canvasRef} className="pointer-events-none absolute inset-0 z-10 h-full w-full" />
          <CardContent result={result} />
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   Variant Definitions
   ═══════════════════════════════════════════════ */

/* 1. Current — shimmer + edge glow (baseline) */
function CurrentOverlay(hovering: boolean, mx: number, my: number) {
  return (
    <>
      <div className="pointer-events-none absolute -inset-px rounded-2xl transition-opacity duration-300 z-[-1]"
        style={{ opacity: hovering ? 1 : 0, background: `radial-gradient(circle at ${mx}% ${my}%, rgba(255,255,255,0.6), rgba(255,255,255,0.12) 40%, var(--border) 70%)` }} />
      <div className="pointer-events-none absolute inset-0 z-10 transition-opacity duration-300"
        style={{ opacity: hovering ? 0.06 : 0, background: `radial-gradient(circle at ${mx}% ${my}%, white, transparent 60%)` }} />
    </>
  );
}

/* 2. Holographic rainbow shimmer */
function HoloOverlay(hovering: boolean, mx: number, my: number) {
  return (
    <div className="pointer-events-none absolute inset-0 z-10 transition-opacity duration-300"
      style={{
        opacity: hovering ? 0.12 : 0,
        background: `conic-gradient(from ${mx * 3.6}deg at ${mx}% ${my}%,
          rgba(255,0,0,0.3), rgba(255,255,0,0.3), rgba(0,255,0,0.3),
          rgba(0,255,255,0.3), rgba(0,0,255,0.3), rgba(255,0,255,0.3), rgba(255,0,0,0.3))`,
        mixBlendMode: 'screen',
      }}
    />
  );
}

/* 3. Spotlight — hard circle reveal */
function SpotlightOverlay(hovering: boolean, mx: number, my: number) {
  return (
    <div className="pointer-events-none absolute inset-0 z-10 transition-opacity duration-200"
      style={{
        opacity: hovering ? 1 : 0,
        background: `radial-gradient(circle 100px at ${mx}% ${my}%, transparent 0%, rgba(0,0,0,0.4) 100%)`,
      }}
    />
  );
}

/* 4. Noise grain */
function GrainOverlay(hovering: boolean) {
  return (
    <div className="pointer-events-none absolute inset-0 z-10 transition-opacity duration-300"
      style={{
        opacity: hovering ? 0.06 : 0.025,
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        backgroundSize: '128px 128px',
      }}
    />
  );
}

/* 5. Dual-tone gradient sweep */
function GradientSweepOverlay(hovering: boolean, mx: number, my: number) {
  const angle = Math.round(mx * 1.8 + my * 1.8);
  return (
    <div className="pointer-events-none absolute inset-0 z-10 transition-opacity duration-300"
      style={{
        opacity: hovering ? 0.07 : 0,
        background: `linear-gradient(${angle}deg, var(--score-high), var(--score-mid), var(--score-low))`,
      }}
    />
  );
}

/* 6. Topographic contour (canvas) */
function drawTopo(ctx: CanvasRenderingContext2D, w: number, h: number, mx: number, my: number, hovering: boolean) {
  if (!hovering) return;
  const dark = document.documentElement.classList.contains('dark');
  const base = dark ? 'rgba(255,255,255,' : 'rgba(0,0,0,';
  for (let r = 20; r < 300; r += 16) {
    ctx.beginPath();
    ctx.strokeStyle = `${base}${Math.max(0.015, 0.1 - r * 0.0003)})`;
    ctx.lineWidth = 0.5;
    for (let a = 0; a < Math.PI * 2; a += 0.02) {
      const noise = Math.sin(a * 3 + r * 0.05) * 8 + Math.cos(a * 5 - r * 0.03) * 6;
      const x = mx + (r + noise) * Math.cos(a);
      const y = my + (r + noise) * Math.sin(a) * 0.7;
      a === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.stroke();
  }
}

/* 7. Grid warp (canvas) */
function drawGridWarp(ctx: CanvasRenderingContext2D, w: number, h: number, mx: number, my: number, hovering: boolean) {
  const dark = document.documentElement.classList.contains('dark');
  ctx.strokeStyle = dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.04)';
  ctx.lineWidth = 0.5;
  const sp = 20;
  const warpR = hovering ? 80 : 0;

  const warp = (px: number, py: number) => {
    const dx = px - mx, dy = py - my;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < warpR && dist > 0) {
      const f = (1 - dist / warpR) * 14;
      return { x: px + (dx / dist) * f, y: py + (dy / dist) * f };
    }
    return { x: px, y: py };
  };

  for (let y = 0; y <= h; y += sp) {
    ctx.beginPath();
    for (let x = 0; x <= w; x += 2) {
      const p = warp(x, y);
      x === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
  }
  for (let x = 0; x <= w; x += sp) {
    ctx.beginPath();
    for (let y = 0; y <= h; y += 2) {
      const p = warp(x, y);
      y === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
  }
}

/* 8. Dot reveal (canvas) */
function drawDotReveal(ctx: CanvasRenderingContext2D, w: number, h: number, mx: number, my: number, hovering: boolean) {
  if (!hovering) return;
  const dark = document.documentElement.classList.contains('dark');
  const c = dark ? 255 : 0;
  const spacing = 12;
  const reveal = 120;

  for (let x = spacing / 2; x < w; x += spacing) {
    for (let y = spacing / 2; y < h; y += spacing) {
      const dx = x - mx, dy = y - my;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist > reveal) continue;
      const prox = 1 - dist / reveal;
      ctx.fillStyle = `rgba(${c},${c},${c},${prox * prox * 0.4})`;
      ctx.beginPath();
      ctx.arc(x, y, 0.8 + prox * 0.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

/* 9. Circuit board (canvas) */
function drawCircuit(ctx: CanvasRenderingContext2D, w: number, h: number) {
  const dark = document.documentElement.classList.contains('dark');
  ctx.strokeStyle = dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.035)';
  ctx.lineWidth = 0.5;
  const sp = 22;
  const seed = (x: number, y: number) => Math.sin(x * 12.9898 + y * 78.233) * 43758.5453 % 1;

  for (let x = sp; x < w; x += sp) {
    for (let y = sp; y < h; y += sp) {
      const s = Math.abs(seed(x, y));
      if (s > 0.6) {
        ctx.beginPath();
        s > 0.8 ? (ctx.moveTo(x, y), ctx.lineTo(x + sp, y)) : (ctx.moveTo(x, y), ctx.lineTo(x, y + sp));
        ctx.stroke();
      }
      if (s > 0.88) {
        ctx.fillStyle = dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)';
        ctx.beginPath();
        ctx.arc(x, y, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }
}

/* 10. Crosshatch lines (canvas) */
function drawCrosshatch(ctx: CanvasRenderingContext2D, w: number, h: number, mx: number, my: number, hovering: boolean) {
  if (!hovering) return;
  const dark = document.documentElement.classList.contains('dark');
  const c = dark ? 'rgba(255,255,255,' : 'rgba(0,0,0,';
  const sp = 10;
  const reveal = 140;

  for (let i = -h; i < w + h; i += sp) {
    const cx = i + h / 2, cy = h / 2;
    const dist = Math.sqrt((cx - mx) ** 2 + (cy - my) ** 2);
    if (dist > reveal) continue;
    const alpha = (1 - dist / reveal) * 0.08;
    ctx.strokeStyle = `${c}${alpha})`;
    ctx.lineWidth = 0.5;
    // Diagonal /
    ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i + h, h); ctx.stroke();
    // Diagonal \
    ctx.beginPath(); ctx.moveTo(i, h); ctx.lineTo(i + h, 0); ctx.stroke();
  }
}

/* 11. Scanlines */
function ScanlinesOverlay(hovering: boolean) {
  return (
    <div className="pointer-events-none absolute inset-0 z-10 transition-opacity duration-300"
      style={{
        opacity: hovering ? 0.04 : 0.015,
        backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, currentColor 2px, currentColor 3px)',
        backgroundSize: '100% 3px',
      }}
    />
  );
}

/* 12. Prismatic edge glow */
function PrismaticOverlay(hovering: boolean, mx: number, my: number) {
  return (
    <>
      <div className="pointer-events-none absolute -inset-px rounded-2xl transition-opacity duration-300 z-[-1]"
        style={{
          opacity: hovering ? 1 : 0,
          background: `conic-gradient(from ${mx * 3.6}deg at ${mx}% ${my}%,
            rgba(255,100,100,0.5), rgba(255,255,100,0.5), rgba(100,255,100,0.5),
            rgba(100,255,255,0.5), rgba(100,100,255,0.5), rgba(255,100,255,0.5), rgba(255,100,100,0.5))`,
        }}
      />
      <div className="pointer-events-none absolute -inset-px rounded-2xl transition-opacity duration-300 z-[-1]"
        style={{ opacity: hovering ? 0 : 1, background: 'var(--border)' }}
      />
      <div className="absolute inset-px rounded-[15px] bg-card z-[-1]" />
    </>
  );
}

/* ═══════════════════════════════════════════════
   Page
   ═══════════════════════════════════════════════ */

export default function CardVariants() {
  useEffect(() => { document.title = 'Score Card Variants — Reepo.dev'; }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="mb-12">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Score Card Variants</h1>
        <p className="mt-2 text-[14px] text-muted-foreground">
          Same card layout, different surface effects. Hover to interact.
        </p>
      </div>

      <div className="space-y-14">
        <VariantShell title="1. Current — Shimmer + Edge Glow" overlay={CurrentOverlay} result={MOCK} />
        <VariantShell title="2. Holographic Rainbow" overlay={HoloOverlay} result={MOCK} />
        <VariantShell title="3. Spotlight" overlay={SpotlightOverlay} result={MOCK} />
        <VariantShell title="4. Film Grain" overlay={(h) => GrainOverlay(h)} result={MOCK} />
        <VariantShell title="5. Gradient Sweep" overlay={GradientSweepOverlay} result={MOCK} />
        <CanvasShell title="6. Topographic Contour" draw={drawTopo} result={MOCK} />
        <CanvasShell title="7. Grid Warp" draw={drawGridWarp} result={MOCK} />
        <CanvasShell title="8. Dot Reveal" draw={drawDotReveal} result={MOCK} />
        <CanvasShell title="9. Circuit Board" draw={drawCircuit} result={MOCK} />
        <CanvasShell title="10. Crosshatch Reveal" draw={drawCrosshatch} result={MOCK} />
        <VariantShell title="11. Scanlines" overlay={(h) => ScanlinesOverlay(h)} result={MOCK} />
        <VariantShell title="12. Prismatic Edge" overlay={PrismaticOverlay} result={MOCK} />
      </div>
    </div>
  );
}
