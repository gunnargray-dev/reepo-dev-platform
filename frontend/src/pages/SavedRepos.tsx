import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark } from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { getBookmarks } from '@/lib/api'
import type { Repo } from '@/lib/api'
import { RepoCard } from '@/components/repo-card'
import { Button } from '@/components/ui/button'

export default function SavedRepos() {
  const { user, loading: authLoading, signIn } = useAuth()
  const [repos, setRepos] = useState<Repo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) return
    setLoading(true)
    getBookmarks()
      .then(setRepos)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user])

  if (authLoading) return null

  if (!user) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-20 text-center sm:px-6">
        <Bookmark className="mx-auto h-10 w-10 text-muted-foreground" />
        <h1 className="mt-4 text-xl font-semibold">Saved Repos</h1>
        <p className="mt-2 text-[14px] text-muted-foreground">Sign in to save repos and access them later.</p>
        <Button className="mt-4" onClick={signIn}>Sign in with GitHub</Button>
      </div>
    )
  }

  if (loading) return null

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <h1 className="text-xl font-semibold">Saved Repos</h1>
      <p className="mt-1 text-[14px] text-muted-foreground">{repos.length} saved</p>
      {repos.length === 0 ? (
        <div className="mt-12 text-center">
          <p className="text-muted-foreground">No saved repos yet.</p>
          <Button asChild variant="outline" className="mt-4">
            <Link to="/search">Browse repos</Link>
          </Button>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-2">
          {repos.map((r) => <RepoCard key={r.id} repo={r} />)}
        </div>
      )}
    </div>
  )
}
