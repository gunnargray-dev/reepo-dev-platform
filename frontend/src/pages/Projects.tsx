import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Rocket, ArrowUpRight, ChevronUp, Plus } from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { getProjects, upvoteProject } from '@/lib/api'
import type { Project } from '@/lib/api'
import { Button } from '@/components/ui/button'

export default function Projects() {
  const { user, signIn } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [sort, setSort] = useState<'upvotes' | 'newest'>('upvotes')

  useEffect(() => {
    setLoading(true)
    getProjects(sort)
      .then(setProjects)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [sort])

  const handleUpvote = async (id: number) => {
    if (!user) { signIn(); return }
    try {
      const { upvoted } = await upvoteProject(id)
      setProjects((prev) =>
        prev.map((p) =>
          p.id === id
            ? { ...p, upvote_count: p.upvote_count + (upvoted ? 1 : -1) }
            : p
        )
      )
    } catch {}
  }

  if (loading) return null

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Projects</h1>
          <p className="mt-1 text-[14px] text-muted-foreground">Built with open-source AI repos</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-border text-[13px] overflow-hidden">
            <button
              onClick={() => setSort('upvotes')}
              className={`px-3 py-1.5 transition-colors ${sort === 'upvotes' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Top
            </button>
            <button
              onClick={() => setSort('newest')}
              className={`px-3 py-1.5 transition-colors ${sort === 'newest' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              New
            </button>
          </div>
          {user && (
            <Button asChild size="sm">
              <Link to="/projects/new"><Plus className="mr-1.5 h-3 w-3" />Submit</Link>
            </Button>
          )}
        </div>
      </div>

      {projects.length === 0 ? (
        <div className="mt-12 text-center">
          <Rocket className="mx-auto h-10 w-10 text-muted-foreground" />
          <p className="mt-4 text-muted-foreground">No projects yet. Be the first to share what you've built!</p>
          {user ? (
            <Button asChild className="mt-4"><Link to="/projects/new">Submit a project</Link></Button>
          ) : (
            <Button className="mt-4" onClick={signIn}>Sign in to submit</Button>
          )}
        </div>
      ) : (
        <div className="mt-6 space-y-2">
          {projects.map((p) => (
            <div
              key={p.id}
              className="flex items-start gap-4 rounded-lg border border-border/60 bg-card px-4 py-3.5 transition-all hover:border-border/80"
            >
              <button
                onClick={() => handleUpvote(p.id)}
                className="flex flex-col items-center shrink-0 rounded-md border border-border px-2 py-1 text-[12px] hover:bg-accent/10 transition-colors"
              >
                <ChevronUp className="h-4 w-4" />
                <span className="font-medium">{p.upvote_count}</span>
              </button>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-[15px] font-medium text-foreground">{p.title}</h3>
                  {p.url && (
                    <a
                      href={p.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
                {p.description && (
                  <p className="mt-1 text-[13px] text-muted-foreground line-clamp-2">{p.description}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
