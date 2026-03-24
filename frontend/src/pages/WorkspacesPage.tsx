import { FormEvent, useEffect, useState } from 'react'
import { apiRequest } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

type Workspace = {
  id: number
  name: string
  slug: string
  created_at: string
}

export default function WorkspacesPage() {
  const { token, workspace, setWorkspace, refreshWorkspaces } = useAuth()
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const loadWorkspaces = async () => {
    if (!token) return
    setLoading(true)
    setError('')

    try {
      const data = (await apiRequest('/workspaces', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })) as Workspace[]

      setWorkspaces(data)

      if (data.length > 0 && !workspace) {
        setWorkspace(data[0])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workspaces')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadWorkspaces()
  }, [token])

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault()
    if (!token) return

    setSubmitting(true)
    setError('')
    setSuccess('')

    try {
      const created = (await apiRequest('/workspaces', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name }),
      })) as Workspace

      setName('')
      await refreshWorkspaces()
      setWorkspace(created)
      setSuccess(`Workspace "${created.name}" created and selected.`)
      await loadWorkspaces()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create workspace')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="grid">
      <div className="card">
        <h2>Your workspaces</h2>
        {loading ? (
          <p className="muted">Loading...</p>
        ) : workspaces.length === 0 ? (
          <p className="muted">No workspaces yet.</p>
        ) : (
          <div className="workspace-list">
            {workspaces.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`workspace-row${workspace?.id === item.id ? ' workspace-row-active' : ''}`}
                onClick={() => {
                  setWorkspace(item)
                  setSuccess(`Selected "${item.name}".`)
                }}
              >
                <div>
                  <div className="workspace-name">{item.name}</div>
                  <div className="workspace-slug">{item.slug}</div>
                </div>
                {workspace?.id === item.id ? (
                  <div className="workspace-badge">Active</div>
                ) : null}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2>Create workspace</h2>
        <form onSubmit={handleCreate} className="stack">
          <label className="field">
            <span>Workspace name</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              minLength={2}
              required
            />
          </label>

          {success ? <div className="success-box">{success}</div> : null}
          {error ? <div className="error-box">{error}</div> : null}

          <button className="button" type="submit" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create workspace'}
          </button>
        </form>
      </div>
    </div>
  )
}
