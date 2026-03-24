import { useAuth } from '../contexts/AuthContext'

export default function DashboardPage() {
  const { user, workspace } = useAuth()

  return (
    <div className="grid">
      <div className="card hero-card">
        <h2>Welcome back</h2>
        <p className="hero-copy">
          {user?.full_name}, your Phase 1 SaaS foundation is live.
        </p>
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
