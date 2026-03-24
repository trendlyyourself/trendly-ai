import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { token, loading } = useAuth()

  if (loading) {
    return <div className="screen-center">Loading...</div>
  }

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return children
}
