export type User = {
  id: string
  full_name: string
  email: string
}

export type Workspace = {
  id: string
  name: string
  slug: string
  role: string
}

export type AuthResponse = {
  access_token: string
  token_type: string
  user: User
  workspace: Workspace | null
}
