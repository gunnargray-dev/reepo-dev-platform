import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Send, X, AlertCircle, Bookmark, Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { postSSE } from '@/lib/sse';
import { getAccessToken } from '@/lib/auth';
import {
  StackPickCard,
  IntentChips,
  type BuildIntent as Intent,
  type StackPick as Pick,
} from '@/components/AIStack';

const EXAMPLES = [
  'real-time vector search',
  'local LLM agent with tools',
  'multimodal product search',
  'summarize PDFs locally',
];

interface DoneEvent {
  total_picks: number;
  notes?: string;
}

type Status = 'idle' | 'streaming' | 'done' | 'error';

export default function Build() {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [intent, setIntent] = useState<Intent | null>(null);
  const [picks, setPicks] = useState<Pick[]>([]);
  const [degraded, setDegraded] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [doneInfo, setDoneInfo] = useState<DoneEvent | null>(null);
  const [cacheHit, setCacheHit] = useState(false);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error' | 'copied'>('idle');
  const [savedSlug, setSavedSlug] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    document.title = 'Build a Stack -- Reepo';
  }, []);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  function reset() {
    setIntent(null);
    setPicks([]);
    setDegraded(false);
    setErrorMsg(null);
    setDoneInfo(null);
    setCacheHit(false);
    setSaveState('idle');
    setSavedSlug(null);
  }

  async function runQuery(q: string) {
    const trimmed = q.trim();
    if (!trimmed) return;
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    reset();
    setStatus('streaming');

    try {
      await postSSE(
        '/api/build',
        { query: trimmed },
        (e) => {
          switch (e.event) {
            case 'cache':
              setCacheHit(true);
              break;
            case 'intent':
              setIntent(e.data as Intent);
              break;
            case 'degraded':
              setDegraded(true);
              break;
            case 'candidates':
              if ((e.data as { degraded?: boolean })?.degraded) setDegraded(true);
              break;
            case 'pick':
              setPicks((prev) => [...prev, e.data as Pick]);
              break;
            case 'done':
              setDoneInfo(e.data as DoneEvent);
              setStatus('done');
              break;
            case 'error': {
              const msg = (e.data as { message?: string })?.message ?? 'Unknown error';
              setErrorMsg(msg);
              setStatus('error');
              break;
            }
          }
        },
        ac.signal,
      );
      // If the stream ended without a `done` event, settle status.
      setStatus((prev) => (prev === 'streaming' ? 'done' : prev));
    } catch (err) {
      if (ac.signal.aborted) return;
      setErrorMsg(err instanceof Error ? err.message : String(err));
      setStatus('error');
    }
  }

  function onExample(q: string) {
    setQuery(q);
    runQuery(q);
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    runQuery(query);
  }

  function onCancel() {
    abortRef.current?.abort();
    setStatus((prev) => (prev === 'streaming' ? 'idle' : prev));
  }

  async function onSaveCollection() {
    setSaveState('saving');
    try {
      const token = await getAccessToken();
      if (!token) {
        setSaveState('error');
        setErrorMsg('Please sign in to save a collection.');
        return;
      }
      const baseSlug = query
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 40) || 'build-stack';
      const slug = `${baseSlug}-${Date.now().toString(36).slice(-4)}`;
      const name = query.trim().slice(0, 60) || 'Build Stack';
      const res = await fetch('/api/collections', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name, slug, description: `AI-generated stack for: ${query.trim()}`, is_public: true }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Save failed: ${res.status}`);
      }
      const created = (await res.json()) as { id: number; slug: string };
      // Add each pick.
      await Promise.all(
        picks.map((p) =>
          fetch(`/api/collections/${created.id}/repos`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ repo_id: p.repo_id }),
          }).catch(() => null),
        ),
      );
      setSavedSlug(created.slug);
      setSaveState('saved');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Save failed');
      setSaveState('error');
    }
  }

  async function onCopyJson() {
    const payload = {
      query,
      intent,
      picks,
      notes: doneInfo?.notes ?? '',
    };
    try {
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      setSaveState('copied');
    } catch {
      setSaveState('error');
    }
  }

  const isStreaming = status === 'streaming';

  return (
    <div className="relative">
      {/* Hero */}
      <section className="relative z-10 px-4 pt-16 pb-10 sm:pt-24">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-5xl leading-[1.1] motion-safe:animate-slide-up">
            Describe what you want to build
          </h1>
          <p
            className="mt-3 text-[15px] text-muted-foreground motion-safe:animate-slide-up"
            style={{ animationDelay: '120ms' }}
          >
            We'll recommend the right open-source stack.
          </p>

          <form
            onSubmit={onSubmit}
            className="mt-8 motion-safe:animate-slide-up"
            style={{ animationDelay: '200ms' }}
          >
            <label htmlFor="build-query" className="sr-only">
              Describe your project
            </label>
            <div className="relative rounded-xl border border-border/60 bg-background focus-within:border-border transition-colors">
              <textarea
                id="build-query"
                ref={textareaRef}
                rows={3}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault();
                    runQuery(query);
                  }
                }}
                placeholder="e.g. I want to build a local RAG app with citations…"
                className="w-full resize-none bg-transparent px-4 py-3 text-[14.5px] text-foreground placeholder:text-muted-foreground/70 outline-none"
                disabled={isStreaming}
              />
              <div className="flex items-center justify-between border-t border-border/60 px-3 py-2">
                <span className="text-[11px] text-muted-foreground">
                  Cmd/Ctrl+Enter to submit
                </span>
                {isStreaming ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={onCancel}
                    aria-label="Cancel build"
                  >
                    <X className="h-3.5 w-3.5" />
                    Cancel
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    size="sm"
                    disabled={!query.trim()}
                    aria-label="Submit build query"
                  >
                    <Send className="h-3.5 w-3.5" />
                    Build
                  </Button>
                )}
              </div>
            </div>
          </form>

          <div
            className="mt-4 flex flex-wrap items-center justify-center gap-1.5 motion-safe:animate-slide-up"
            style={{ animationDelay: '280ms' }}
          >
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => onExample(ex)}
                disabled={isStreaming}
                className="rounded-full border border-border/60 px-3 py-1 text-[12px] text-muted-foreground transition-colors hover:border-border hover:text-foreground hover:bg-accent/10 disabled:opacity-50"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Streaming results */}
      {(status !== 'idle' || picks.length > 0) && (
        <section
          className="relative z-10 mx-auto max-w-3xl px-4 pb-20 sm:px-6"
          aria-live="polite"
          aria-busy={isStreaming}
        >
          {cacheHit && (
            <div className="mb-4 text-[11px] uppercase tracking-wider text-muted-foreground">
              Cached result
            </div>
          )}

          {/* Intent chips */}
          <IntentChips intent={intent} />

          {/* Degraded notice */}
          {degraded && (
            <div className="mb-4 flex items-start gap-2 rounded-lg border border-border/60 bg-muted/40 px-3 py-2 text-[12.5px] text-muted-foreground">
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>
                Semantic search unavailable — using keyword fallback. Add{' '}
                <code className="rounded bg-muted px-1 py-0.5 text-[11px]">VOYAGE_API_KEY</code> to enable.
              </span>
            </div>
          )}

          {/* Error */}
          {errorMsg && status === 'error' && (
            <div
              role="alert"
              className="mb-4 flex items-start gap-2 rounded-lg border border-destructive/60 bg-destructive/10 px-3 py-2 text-[12.5px] text-destructive"
            >
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Stack */}
          {(picks.length > 0 || isStreaming) && (
            <div>
              <h2 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted-foreground">
                Stack
              </h2>
              <div className="grid gap-3">
                {picks.map((pick, i) => (
                  <StackPickCard key={`${pick.repo_id}-${i}`} pick={pick} index={i} />
                ))}
                {isStreaming &&
                  Array.from({ length: Math.max(1, 3 - picks.length) }).map((_, i) => (
                    <Skeleton key={`sk-${i}`} className="h-[120px] rounded-xl" />
                  ))}
              </div>
            </div>
          )}

          {/* Done actions */}
          {status === 'done' && picks.length > 0 && (
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button
                onClick={onSaveCollection}
                disabled={saveState === 'saving' || saveState === 'saved'}
                size="sm"
              >
                {saveState === 'saved' ? <Check className="h-3.5 w-3.5" /> : <Bookmark className="h-3.5 w-3.5" />}
                {saveState === 'saving'
                  ? 'Saving…'
                  : saveState === 'saved'
                    ? 'Saved'
                    : 'Save as collection'}
              </Button>
              <Button onClick={onCopyJson} variant="outline" size="sm">
                {saveState === 'copied' ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {saveState === 'copied' ? 'Copied' : 'Copy stack as JSON'}
              </Button>
              {savedSlug && (
                <span className="text-[12.5px] text-muted-foreground">
                  Saved. <Link to="/saved" className="underline hover:text-foreground">View collections</Link>
                </span>
              )}
              {doneInfo?.notes && (
                <p className="mt-3 w-full text-[12.5px] text-muted-foreground italic">{doneInfo.notes}</p>
              )}
            </div>
          )}

          {status === 'done' && picks.length === 0 && !errorMsg && (
            <p className="text-[13px] text-muted-foreground">
              No stack picks were produced. Try rephrasing the query.
            </p>
          )}
        </section>
      )}

      {/* Footer hint when idle */}
      {status === 'idle' && (
        <section className="relative z-10 mx-auto max-w-2xl px-4 pb-20 text-center">
          <div className="mx-auto h-px w-24 bg-gradient-to-r from-transparent via-border to-transparent mb-8" />
          <p className="inline-flex items-center gap-1.5 text-[12px] text-muted-foreground">
            <Sparkles className="h-3 w-3" />
            Powered by Reepo's open-source index
          </p>
        </section>
      )}
    </div>
  );
}
