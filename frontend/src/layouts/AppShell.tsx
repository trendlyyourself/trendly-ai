import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function AppShell() {
  const { user, workspace, logout } = useAuth()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <Link to="/" className="brand">
            Trendly AI
          </Link>

          <nav className="nav">
            <NavLink to="/app/dashboard" className="nav-link">
              Dashboard
            </NavLink>
            <NavLink to="/app/workspaces" className="nav-link">
              Workspaces
            </NavLink>
          </nav>
        </div>

        <div className="sidebar-footer">
          <div className="workspace-chip">{workspace?.name ?? 'No workspace'}</div>
          <button className="button button-secondary" onClick={logout}>
            Log out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <h1 className="topbar-title">Operations</h1>
            <p className="topbar-subtitle">Production-ready foundation</p>
          </div>

          <div className="profile-box">
            <div className="profile-name">{user?.full_name}</div>
            <div className="profile-email">{user?.email}</div>
          </div>
        </header>

        <section className="page-content">
          <Outlet />
        </section>
      </main>
    </div>
  )
}
