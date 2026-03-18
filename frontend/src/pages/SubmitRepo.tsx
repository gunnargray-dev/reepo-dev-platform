import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth'
import { submitRepo, getMySubmissions } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FolderPlus, Check, AlertCircle } from 'lucide-react'

const GITHUB_URL_RE = /^https?:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/

export default function SubmitRepo() {
  const { user, loading: authLoading, signIn } = useAuth()
  const [url, setUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [submissions, setSubmissions] = useState<any[]>([])

  useEffect(() => {
    if (!user) return
    getMySubmissions().then(setSubmissions).catch(() => {})
  }, [user])

  if (authLoading) return null

  if (!user) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-20 text-center sm:px-6">
        <FolderPlus className="mx-auto h-10 w-10 text-muted-foreground" />
        <h1 className="mt-4 text-xl font-semibold">Submit a Repo</h1>
        <p className="mt-2 text-[14px] text-muted-foreground">Sign in to submit repos for indexing.</p>
        <Button className="mt-4" onClick={signIn}>Sign in with GitHub</Button>
      </div>
    )
  }

  const isValid = GITHUB_URL_RE.test(url.trim())

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid) return
    setSubmitting(true)
    setResult(null)
    try {
      await submitRepo(url.trim())
      setResult({ ok: true, message: 'Repo submitted for review!' })
      setUrl('')
      getMySubmissions().then(setSubmissions).catch(() => {})
    } catch (err: any) {
      setResult({ ok: false, message: err.message || 'Submission failed' })
    } finally {
      setSubmitting(false)
    }
  }

  const statusColor = (status: string) => {
    if (status === 'approved') return 'bg-[var(--score-high)]/10 text-[var(--score-high)]'
    if (status === 'rejected') return 'bg-[var(--score-low)]/10 text-[var(--score-low)]'
    return 'bg-[var(--score-mid)]/10 text-[var(--score-mid)]'
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold">Submit a Repo</h1>
      <p className="mt-1 text-[14px] text-muted-foreground">
        Know an open-source AI repo that should be indexed? Submit it here.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 flex gap-2">
        <Input
          placeholder="https://github.com/owner/repo"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1"
        />
        <Button type="submit" disabled={!isValid || submitting}>
          {submitting ? 'Submitting...' : 'Submit'}
        </Button>
      </form>

      {result && (
        <div className={`mt-3 flex items-center gap-2 text-[13px] ${result.ok ? 'text-[var(--score-high)]' : 'text-[var(--score-low)]'}`}>
          {result.ok ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
          {result.message}
        </div>
      )}

      {submissions.length > 0 && (
        <div className="mt-10">
          <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground mb-3">Your Submissions</h2>
          <div className="space-y-2">
            {submissions.map((s: any) => (
              <div key={s.id} className="flex items-center justify-between rounded-lg border border-border/60 px-4 py-3 text-[14px]">
                <span className="truncate text-foreground">{s.github_url}</span>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium ${statusColor(s.status)}`}>
                  {s.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
