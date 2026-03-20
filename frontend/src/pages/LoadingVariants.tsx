import { useCallback, useEffect, useRef, useState } from 'react';
import { scoreColorVar } from '@/lib/utils';

const DIMS = [
  { label: 'Maintenance', value: 100 },
  { label: 'Docs', value: 45 },
  { label: 'Community', value: 98 },
  { label: 'Popularity', value: 96 },
  { label: 'Freshness', value: 100 },
  { label: 'License', value: 30 },
];
const FINAL_SCORE = 78;

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-4 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{title}</h3>
      <div className="flex items-center justify-center rounded-2xl border border-border/60 bg-card p-10 min-h-[320px]">
        {children}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   1. Rotating Hexagon
   ═══════════════════════════════════════════════ */

function RotatingHexagon() {
  const [activeIdx, setActiveIdx] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIdx((i) => {
        if (i >= 5) { clearInterval(interval); setTimeout(() => setDone(true), 600); return 5; }
        return i + 1;
      });
    }, 700);
    return () => clearInterval(interval);
  }, []);

  const cx = 120, cy = 120, r = 80;
  const points = DIMS.map((_, i) => {
    const angle = (i / 6) * Math.PI * 2 - Math.PI / 2;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  });
  const polyStr = points.map((p) => `${p.x},${p.y}`).join(' ');

  return (
    <div className="flex flex-col items-center gap-6">
      <svg width="240" height="240" viewBox="0 0 240 240" className="transition-transform duration-500" style={{ transform: done ? 'scale(0.9)' : '' }}>
        <g style={{ transformOrigin: '120px 120px', animation: 'spin 8s linear infinite' }}>
          <polygon points={polyStr} fill="none" stroke="var(--border)" strokeWidth="1.5" />
          {points.map((p, i) => {
            const lit = i <= activeIdx;
            const dim = DIMS[i];
            const lx = cx + (r + 28) * Math.cos((i / 6) * Math.PI * 2 - Math.PI / 2);
            const ly = cy + (r + 28) * Math.sin((i / 6) * Math.PI * 2 - Math.PI / 2);
            return (
              <g key={i}>
                <line x1={cx} y1={cy} x2={p.x} y2={p.y} stroke={lit ? scoreColorVar(dim.value) : 'var(--border)'} strokeWidth="1" opacity={lit ? 0.6 : 0.2} />
                <circle cx={p.x} cy={p.y} r={lit ? 5 : 3} fill={lit ? scoreColorVar(dim.value) : 'var(--border)'} style={{ transition: 'all 0.3s' }} />
                <text x={lx} y={ly} textAnchor="middle" dominantBaseline="central" className="text-[9px] font-medium" fill={lit ? 'var(--fg)' : 'var(--fg-muted)'} style={{ transition: 'fill 0.3s' }}>{dim.label}</text>
              </g>
            );
          })}
        </g>
        {done && (
          <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central" className="font-mono text-3xl font-bold" fill={scoreColorVar(FINAL_SCORE)} style={{ animation: 'fade-in 0.4s' }}>{FINAL_SCORE}</text>
        )}
      </svg>
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      {!done && (
        <span className="text-[13px] text-muted-foreground" style={{ animation: 'fade-in 0.3s' }}>
          Analyzing {DIMS[Math.min(activeIdx, 5)].label.toLowerCase()}...
        </span>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════
   2. Code Rain
   ═══════════════════════════════════════════════ */

function CodeRain() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [showScore, setShowScore] = useState(false);
  const startRef = useRef(performance.now());

  const chars = 'ABCDEF0123456789{}[]<>/\\|;:.,MIT Apache BSD GPL stars forks README.md push commit';

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    const dpr = window.devicePixelRatio || 1;
    const w = 400, h = 280;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const cols = Math.floor(w / 14);
    const drops = Array.from({ length: cols }, () => Math.random() * -20);
    const dark = document.documentElement.classList.contains('dark');

    let raf: number;
    const draw = () => {
      const elapsed = performance.now() - startRef.current;
      const slowdown = Math.max(0.15, 1 - elapsed / 4000);

      ctx.fillStyle = dark ? 'rgba(9,9,11,0.12)' : 'rgba(255,255,255,0.12)';
      ctx.fillRect(0, 0, w, h);

      const alpha = Math.max(0.05, 0.7 * slowdown);
      ctx.fillStyle = dark ? `rgba(74,222,128,${alpha})` : `rgba(22,163,74,${alpha})`;
      ctx.font = '12px "Geist Mono", monospace';

      for (let i = 0; i < cols; i++) {
        const char = chars[Math.floor(Math.random() * chars.length)];
        ctx.fillText(char, i * 14, drops[i] * 14);
        if (drops[i] * 14 > h && Math.random() > 0.975) drops[i] = 0;
        drops[i] += slowdown;
      }

      if (elapsed > 4000) {
        setShowScore(true);
        return;
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="relative flex items-center justify-center" style={{ width: 400, height: 280 }}>
      <canvas ref={canvasRef} className="absolute inset-0" />
      {showScore && (
        <div className="relative flex flex-col items-center" style={{ animation: 'fade-in 0.5s' }}>
          <span className="font-mono text-6xl font-bold" style={{ color: scoreColorVar(FINAL_SCORE) }}>{FINAL_SCORE}</span>
          <span className="text-[11px] uppercase tracking-widest text-muted-foreground mt-1">Reepo Score</span>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════
   3. Orbital Rings
   ═══════════════════════════════════════════════ */

function OrbitalRings() {
  const [phase, setPhase] = useState(0); // 0=spinning, 1=collapsing, 2=done

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 3000);
    const t2 = setTimeout(() => setPhase(2), 3800);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  return (
    <div className="relative flex items-center justify-center" style={{ width: 240, height: 240 }}>
      {DIMS.map((dim, i) => {
        const baseR = 30 + i * 16;
        const targetR = phase >= 1 ? 50 : baseR;
        const speed = 3 + i * 1.5;
        const color = scoreColorVar(dim.value);
        return (
          <div
            key={i}
            className="absolute rounded-full border"
            style={{
              width: targetR * 2,
              height: targetR * 2,
              borderColor: phase >= 2 ? 'transparent' : color,
              opacity: phase >= 2 ? 0 : 0.3 + (i <= 3 ? 0.1 : 0),
              animation: phase < 1 ? `spin ${speed}s linear infinite` : undefined,
              transition: 'all 0.8s cubic-bezier(0.16,1,0.3,1)',
            }}
          >
            <div
              className="absolute -top-1 left-1/2 -translate-x-1/2 h-2 w-2 rounded-full"
              style={{ backgroundColor: color, opacity: phase >= 2 ? 0 : 1, transition: 'opacity 0.3s' }}
            />
          </div>
        );
      })}
      {phase >= 2 && (
        <div className="flex flex-col items-center" style={{ animation: 'fade-in 0.5s' }}>
          <span className="font-mono text-5xl font-bold" style={{ color: scoreColorVar(FINAL_SCORE) }}>{FINAL_SCORE}</span>
          <span className="text-[10px] uppercase tracking-widest text-muted-foreground mt-1">Score</span>
        </div>
      )}
      {phase < 2 && (
        <span className="absolute -bottom-8 text-[12px] text-muted-foreground">
          {phase === 0 ? 'Scanning dimensions...' : 'Computing score...'}
        </span>
      )}
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   4. Terminal Typewriter
   ═══════════════════════════════════════════════ */

const TERM_LINES = [
  { text: '$ reepo score anthropics/skills', delay: 0 },
  { text: '', delay: 300 },
  { text: 'Fetching repo metadata...          OK', delay: 500 },
  { text: 'Stars: 97,537  Forks: 10,548      Python', delay: 800 },
  { text: '', delay: 900 },
  { text: 'Analyzing maintenance health...    100', delay: 1200, color: 'var(--score-high)' },
  { text: 'Parsing README (847 chars)...       45', delay: 1700, color: 'var(--score-mid)' },
  { text: 'Measuring community activity...     98', delay: 2200, color: 'var(--score-high)' },
  { text: 'Calculating popularity (log)...     96', delay: 2700, color: 'var(--score-high)' },
  { text: 'Checking freshness...              100', delay: 3100, color: 'var(--score-high)' },
  { text: 'Reviewing license...                30', delay: 3500, color: 'var(--score-low)' },
  { text: '', delay: 3800 },
  { text: '═══════════════════════════════════════', delay: 4000 },
  { text: 'REEPO SCORE                         78', delay: 4200, color: 'var(--score-mid)', bold: true },
  { text: '═══════════════════════════════════════', delay: 4200 },
];

function TerminalTypewriter() {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    TERM_LINES.forEach((line, i) => {
      timers.push(setTimeout(() => setVisibleCount(i + 1), line.delay));
    });
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="w-full max-w-md overflow-hidden rounded-lg border border-white/10 bg-[#0d1117] font-mono text-[12px] leading-relaxed">
      <div className="flex items-center gap-1.5 border-b border-white/10 px-4 py-2">
        <div className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
        <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/80" />
        <div className="h-2.5 w-2.5 rounded-full bg-green-500/80" />
        <span className="ml-2 text-[10px] text-white/30">reepo score</span>
      </div>
      <div className="p-4 text-white/70 min-h-[260px]">
        {TERM_LINES.slice(0, visibleCount).map((line, i) => (
          <div key={i} style={{ color: line.color, fontWeight: (line as any).bold ? 700 : 400, animation: 'fade-in 0.15s' }}>
            {line.text || '\u00A0'}
          </div>
        ))}
        {visibleCount < TERM_LINES.length && (
          <span className="inline-block w-2 h-4 bg-white/60 animate-pulse" />
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   5. Particle Convergence
   ═══════════════════════════════════════════════ */

function ParticleConvergence() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [showScore, setShowScore] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    const dpr = window.devicePixelRatio || 1;
    const w = 300, h = 300;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const dark = document.documentElement.classList.contains('dark');
    const cx = w / 2, cy = h / 2;
    const particles = Array.from({ length: 80 }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      tx: cx + (Math.random() - 0.5) * 30,
      ty: cy + (Math.random() - 0.5) * 30,
      size: 1 + Math.random() * 2,
      speed: 0.01 + Math.random() * 0.02,
    }));

    const start = performance.now();
    let raf: number;

    const draw = () => {
      const elapsed = performance.now() - start;
      const progress = Math.min(elapsed / 3500, 1);

      ctx.clearRect(0, 0, w, h);

      const color = dark ? '255,255,255' : '0,0,0';

      for (const p of particles) {
        const ease = 1 - Math.pow(1 - progress, 3);
        p.x += (p.tx - p.x) * p.speed * (1 + ease * 3);
        p.y += (p.ty - p.y) * p.speed * (1 + ease * 3);

        const dist = Math.sqrt((p.x - cx) ** 2 + (p.y - cy) ** 2);
        const alpha = progress < 0.8 ? 0.4 : Math.max(0, 0.4 * (1 - (progress - 0.8) / 0.2));
        ctx.fillStyle = `rgba(${color},${alpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * (1 - progress * 0.5), 0, Math.PI * 2);
        ctx.fill();

        // Draw connections
        if (dist < 60 && progress < 0.9) {
          ctx.strokeStyle = `rgba(${color},${alpha * 0.3})`;
          ctx.lineWidth = 0.3;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(cx, cy);
          ctx.stroke();
        }
      }

      if (progress >= 1) {
        setShowScore(true);
        return;
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="relative flex items-center justify-center" style={{ width: 300, height: 300 }}>
      <canvas ref={canvasRef} className="absolute inset-0" />
      {showScore && (
        <div className="relative flex flex-col items-center" style={{ animation: 'fade-in 0.5s' }}>
          <span className="font-mono text-6xl font-bold" style={{ color: scoreColorVar(FINAL_SCORE) }}>{FINAL_SCORE}</span>
          <span className="text-[11px] uppercase tracking-widest text-muted-foreground mt-1">Reepo Score</span>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════
   6. Slot Machine
   ═══════════════════════════════════════════════ */

function SlotMachine() {
  const [spinning, setSpinning] = useState(true);
  const [tens, setTens] = useState(0);
  const [ones, setOnes] = useState(0);
  const [tensLocked, setTensLocked] = useState(false);
  const [onesLocked, setOnesLocked] = useState(false);

  useEffect(() => {
    const spinInterval = setInterval(() => {
      if (!tensLocked) setTens(Math.floor(Math.random() * 10));
      if (!onesLocked) setOnes(Math.floor(Math.random() * 10));
    }, 60);

    const t1 = setTimeout(() => { setTens(Math.floor(FINAL_SCORE / 10)); setTensLocked(true); }, 2000);
    const t2 = setTimeout(() => { setOnes(FINAL_SCORE % 10); setOnesLocked(true); setSpinning(false); clearInterval(spinInterval); }, 3000);

    return () => { clearInterval(spinInterval); clearTimeout(t1); clearTimeout(t2); };
  }, []);

  const digitStyle = (locked: boolean) => ({
    color: locked ? scoreColorVar(FINAL_SCORE) : 'var(--fg-muted)',
    transition: locked ? 'color 0.3s' : undefined,
  });

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="flex items-center gap-1">
        <div className="flex h-24 w-16 items-center justify-center rounded-lg border border-border bg-muted/30 overflow-hidden">
          <span className="font-mono text-6xl font-bold tabular-nums" style={digitStyle(tensLocked)}>{tens}</span>
        </div>
        <div className="flex h-24 w-16 items-center justify-center rounded-lg border border-border bg-muted/30 overflow-hidden">
          <span className="font-mono text-6xl font-bold tabular-nums" style={digitStyle(onesLocked)}>{ones}</span>
        </div>
      </div>
      <span className="text-[12px] text-muted-foreground">
        {spinning ? 'Computing score...' : 'Reepo Score'}
      </span>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   7. Expanding Ring Reveal
   ═══════════════════════════════════════════════ */

function ExpandingRing() {
  const [phase, setPhase] = useState(0); // 0=pulse, 1=ring-draw, 2=done
  const [counter, setCounter] = useState(0);
  const frameRef = useRef(0);

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 1500);
    const t2 = setTimeout(() => setPhase(2), 3200);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  useEffect(() => {
    if (phase !== 1) return;
    const start = performance.now();
    const duration = 1500;
    const animate = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCounter(Math.round(FINAL_SCORE * eased));
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [phase]);

  const size = 160;
  const sw = 6;
  const r = (size - sw) / 2;
  const circ = 2 * Math.PI * r;
  const color = scoreColorVar(FINAL_SCORE);
  const offset = phase >= 1 ? circ - (FINAL_SCORE / 100) * circ : circ;

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative" style={{ width: size, height: size }}>
        {/* Pulse rings before draw */}
        {phase === 0 && (
          <>
            <div className="absolute inset-0 rounded-full border border-border animate-ping opacity-20" />
            <div className="absolute inset-4 rounded-full border border-border animate-ping opacity-10" style={{ animationDelay: '0.5s' }} />
          </>
        )}
        <svg width={size} height={size} className="rotate-[-90deg]">
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--border)" strokeWidth={sw} />
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round"
            strokeDasharray={circ} strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1.5s cubic-bezier(0.16,1,0.3,1)' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {phase >= 1 ? (
            <>
              <span className="font-mono text-5xl font-bold" style={{ color }}>{counter}</span>
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground mt-0.5">Score</span>
            </>
          ) : (
            <div className="h-2 w-2 rounded-full bg-muted-foreground animate-pulse" />
          )}
        </div>
        {/* Glow pulse on completion */}
        {phase === 2 && (
          <div className="absolute inset-0 rounded-full" style={{ boxShadow: `0 0 30px ${color}40, 0 0 60px ${color}20`, animation: 'fade-in 0.3s' }} />
        )}
      </div>
      <span className="text-[12px] text-muted-foreground">
        {phase === 0 ? 'Scanning...' : phase === 1 ? 'Computing score...' : 'Done'}
      </span>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   8. Dimension Cascade
   ═══════════════════════════════════════════════ */

function DimensionCascade() {
  const [visibleDims, setVisibleDims] = useState(0);
  const [showTotal, setShowTotal] = useState(false);

  useEffect(() => {
    const timers = DIMS.map((_, i) =>
      setTimeout(() => setVisibleDims(i + 1), 500 + i * 500)
    );
    timers.push(setTimeout(() => setShowTotal(true), 500 + DIMS.length * 500 + 400));
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="w-full max-w-xs space-y-3">
      {DIMS.slice(0, visibleDims).map((dim, i) => {
        const color = scoreColorVar(dim.value);
        return (
          <div key={i} style={{ animation: 'slide-up 0.3s cubic-bezier(0.16,1,0.3,1)' }}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[12px] text-muted-foreground">{dim.label}</span>
              <span className="font-mono text-[13px] font-semibold" style={{ color }}>{dim.value}</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-border/50 overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${dim.value}%`, backgroundColor: color, transition: 'width 0.6s cubic-bezier(0.16,1,0.3,1)' }} />
            </div>
          </div>
        );
      })}
      {showTotal && (
        <div className="pt-3 border-t border-border/60 flex items-center justify-between" style={{ animation: 'slide-up 0.3s' }}>
          <span className="text-[13px] font-medium text-foreground">Reepo Score</span>
          <span className="font-mono text-3xl font-bold" style={{ color: scoreColorVar(FINAL_SCORE) }}>{FINAL_SCORE}</span>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════
   Restart wrapper — lets you replay each animation
   ═══════════════════════════════════════════════ */

function Restartable({ title, children }: { title: string; children: () => React.ReactNode }) {
  const [key, setKey] = useState(0);
  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{title}</h3>
        <button onClick={() => setKey((k) => k + 1)} className="text-[11px] text-muted-foreground hover:text-foreground transition-colors">
          Replay
        </button>
      </div>
      <div className="flex items-center justify-center rounded-2xl border border-border/60 bg-card p-10 min-h-[320px]" key={key}>
        {children()}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   Page
   ═══════════════════════════════════════════════ */

export default function LoadingVariants() {
  useEffect(() => { document.title = 'Loading Variants — Reepo.dev'; }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="mb-12">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Loading State Variants</h1>
        <p className="mt-2 text-[14px] text-muted-foreground">
          Different scanning/scoring animations. Click "Replay" to restart each.
        </p>
      </div>

      <div className="space-y-14">
        <Restartable title="1. Rotating Hexagon">{() => <RotatingHexagon />}</Restartable>
        <Restartable title="2. Code Rain">{() => <CodeRain />}</Restartable>
        <Restartable title="3. Orbital Rings">{() => <OrbitalRings />}</Restartable>
        <Restartable title="4. Terminal Typewriter">{() => <TerminalTypewriter />}</Restartable>
        <Restartable title="5. Particle Convergence">{() => <ParticleConvergence />}</Restartable>
        <Restartable title="6. Slot Machine">{() => <SlotMachine />}</Restartable>
        <Restartable title="7. Expanding Ring Reveal">{() => <ExpandingRing />}</Restartable>
        <Restartable title="8. Dimension Cascade">{() => <DimensionCascade />}</Restartable>
      </div>
    </div>
  );
}
