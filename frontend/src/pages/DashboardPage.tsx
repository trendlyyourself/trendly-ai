import { FormEvent, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { apiRequest } from '../lib/api'

type GenerateResponse = {
  text: string
}

export default function DashboardPage() {
  const { user, workspace, token } = useAuth()
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async (event: FormEvent) => {
    event.preventDefault()
    if (!token || !prompt.trim()) return

    setLoading(true)
    setError('')
    setResult('')

    try {
      const response = (await apiRequest('/ai/generate', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ prompt: prompt.trim() }),
      })) as GenerateResponse

      setResult(response.text)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'OpenAI request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid">
      <div className="card hero-card">
        <h2>Welcome back</h2>
        <p className="hero-copy">
          {user?.full_name}, your Trendly AI workspace is ready.
        </p>
      </div>

      <div className="card">
        <h2>AI assistant</h2>
        <p className="muted">Send a prompt through the authenticated Trendly backend.</p>
        <form onSubmit={generate}>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Ask Trendly AI to analyze or improve something..."
            rows={5}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !prompt.trim()}>
            {loading ? 'Generating…' : 'Generate'}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
        {result && (
          <div className="profile-box">
            <div className="profile-name">Trendly AI</div>
            <div className="profile-email">{result}</div>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Active workspace</h2>
        {workspace ? (
          <div className="workspace-row workspace-row-active">
            <div>
              <div className="workspace-name">{workspace.name}</div>
              <div className="workspace-slug">{workspace.slug}</div>
            </div>
            <div className="workspace-badge">Active</div>
          </div>
        ) : (
          <p className="muted">No active workspace selected.</p>
        )}
      </div>

      <div className="card">
        <h2>Account</h2>
        <div className="profile-box">
          <div className="profile-name">{user?.full_name}</div>
          <div className="profile-email">{user?.email}</div>
        </div>
      </div>
    </div>
  )
}
