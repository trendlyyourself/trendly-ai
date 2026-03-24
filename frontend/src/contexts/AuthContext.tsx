import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from 'react'
import { apiRequest } from '../lib/api'

type User = {
  id: number
  full_name: string
  email: string
  created_at: string
}

type Workspace = {
  id: number
  name: string
  slug: string
  created_at: string
}

type AuthResponse = {
  access_token: string
  token_type: string
  user: User
}

type AuthContextType = {
  token: string | null
  user: User | null
  workspace: Workspace | null
  workspaces: Workspace[]
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (fullName: string, email: string, password: string) => Promise<void>
  logout: () => void
  refreshWorkspaces: () => Promise<void>
  setWorkspace: (workspace: Workspace | null) => void
}

const TOKEN_KEY = 'access_token'
const USER_KEY = 'user'
const WORKSPACE_KEY = 'workspace'

const AuthContext = createContext<AuthContextType | null>(null)

function parseJson<T>(value: string | null): T | null {
  if (!value) return null
  try {
    return JSON.parse(value) as T
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [workspace, setWorkspaceState] = useState<Workspace | null>(null)
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [loading, setLoading] = useState(true)

  const setWorkspace = (nextWorkspace: Workspace | null) => {
    setWorkspaceState(nextWorkspace)
    if (nextWorkspace) {
      localStorage.setItem(WORKSPACE_KEY, JSON.stringify(nextWorkspace))
    } else {
      localStorage.removeItem(WORKSPACE_KEY)
    }
  }

  const refreshWorkspaces = async () => {
    if (!token) {
      setWorkspaces([])
      setWorkspace(null)
      return
    }

    const data = (await apiRequest('/workspaces', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })) as Workspace[]

    setWorkspaces(data)

    if (data.length === 0) {
      setWorkspace(null)
      return
    }

    const savedWorkspace = parseJson<Workspace>(localStorage.getItem(WORKSPACE_KEY))
    const matchedWorkspace = savedWorkspace
      ? data.find((item) => item.id === savedWorkspace.id) || null
      : null

    setWorkspace(matchedWorkspace || data[0])
  }

  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    const savedUser = parseJson<User>(localStorage.getItem(USER_KEY))
    const savedWorkspace = parseJson<Workspace>(localStorage.getItem(WORKSPACE_KEY))

    setToken(savedToken)
    setUser(savedUser)
    setWorkspaceState(savedWorkspace)
    setLoading(false)
  }, [])

  useEffect(() => {
    if (!token) {
      setWorkspaces([])
      setWorkspace(null)
      return
    }

    void refreshWorkspaces()
  }, [token])

  const applyAuth = (payload: AuthResponse) => {
    setToken(payload.access_token)
    setUser(payload.user)

    localStorage.setItem(TOKEN_KEY, payload.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(payload.user))
  }

  const login = async (email: string, password: string) => {
    const payload = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })

    applyAuth(payload as AuthResponse)
  }

  const signup = async (fullName: string, email: string, password: string) => {
    const payload = await apiRequest('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
      }),
    })

    applyAuth(payload as AuthResponse)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    setWorkspace(null)
    setWorkspaces([])

    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem(WORKSPACE_KEY)
  }

  const value = useMemo(
    () => ({
      token,
      user,
      workspace,
      workspaces,
      loading,
      login,
      signup,
      logout,
      refreshWorkspaces,
      setWorkspace,
    }),
    [token, user, workspace, workspaces, loading]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
