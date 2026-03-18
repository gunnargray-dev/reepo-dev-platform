import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Rocket } from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { submitProject, searchRepos } from '@/lib/api'
import type { Repo } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'

export default function SubmitProject() {
  const { user, loading: authLoading, signIn } = useAuth()
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [url, setUrl] = useState('')
  const [screenshotUrl, setScreenshotUrl] = useState('')
  const [repoSearch, setRepoSearch] = useState('')
  const [repoResults, setRepoResults] = useState<Repo[]>([])
  const [selectedRepos, setSelectedRepos] = useState<Repo[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (authLoading) return null

  if (!user) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-20 text-center sm:px-6">
        <Rocket className="mx-auto h-10 w-10 text-muted-foreground" />
        <h1 className="mt-4 text-xl font-semibold">Submit a Project</h1>
        <p className="mt-2 text-[14px] text-muted-foreground">Sign in to showcase what you've built.</p>
        <Button className="mt-4" onClick={signIn}>Sign in with GitHub</Button>
      </div>
    )
  }

  const handleRepoSearch = async (q: string) => {
    setRepoSearch(q)
    if (q.length < 2) { setRepoResults([]); return }
    try {
      const { repos } = await searchRepos({ q, limit: 5 })
      setRepoResults(repos.filter((r) => !selectedRepos.some((s) => s.id === r.id)))
    } catch {}
  }

  const addRepo = (repo: Repo) => {
    setSelectedRepos((prev) => [...prev, repo])
    setRepoResults((prev) => prev.filter((r) => r.id !== repo.id))
    setRepoSearch('')
  }

  const removeRepo = (id: number) => {
    setSelectedRepos((prev) => prev.filter((r) => r.id !== id))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !description.trim() || !url.trim()) return
    setSubmitting(true)
    setError('')
    try {
      await submitProject({
        title: title.trim(),
        description: description.trim(),
        url: url.trim(),
        repo_ids: selectedRepos.map((r) => r.id),
        screenshot_url: screenshotUrl.trim() || undefined,
      })
      navigate('/projects')
    } catch (err: any) {
      setError(err.message || 'Failed to submit')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold">Submit a Project</h1>
      <p className="mt-1 text-[14px] text-muted-foreground">
        Show off something you built with open-source AI repos.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="text-[13px] font-medium text-foreground">Title</label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="My awesome project" className="mt-1" />
        </div>
        <div>
          <label className="text-[13px] font-medium text-foreground">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What does it do?"
            rows={3}
            className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-[14px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
        <div>
          <label className="text-[13px] font-medium text-foreground">URL</label>
          <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://myproject.com" className="mt-1" />
        </div>
        <div>
          <label className="text-[13px] font-medium text-foreground">Screenshot URL (optional)</label>
          <Input value={screenshotUrl} onChange={(e) => setScreenshotUrl(e.target.value)} placeholder="https://..." className="mt-1" />
        </div>
        <div>
          <label className="text-[13px] font-medium text-foreground">Repos used</label>
          <Input
            value={repoSearch}
            onChange={(e) => handleRepoSearch(e.target.value)}
            placeholder="Search repos..."
            className="mt-1"
          />
          {repoResults.length > 0 && (
            <div className="mt-1 rounded-md border border-border bg-card">
              {repoResults.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => addRepo(r)}
                  className="block w-full text-left px-3 py-2 text-[13px] hover:bg-accent/10 transition-colors"
                >
                  {r.full_name}
                </button>
              ))}
            </div>
          )}
          {selectedRepos.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {selectedRepos.map((r) => (
                <Badge key={r.id} variant="secondary" className="cursor-pointer" onClick={() => removeRepo(r.id)}>
                  {r.full_name} &times;
                </Badge>
              ))}
            </div>
          )}
        </div>

        {error && <p className="text-[13px] text-[var(--score-low)]">{error}</p>}

        <Button type="submit" disabled={!title.trim() || !description.trim() || !url.trim() || submitting}>
          {submitting ? 'Submitting...' : 'Submit Project'}
        </Button>
      </form>
    </div>
  )
}
