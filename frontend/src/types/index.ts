// User types
export interface User {
  id: number
  email: string
  is_admin: boolean
  created_at: string
}

// Migration types
export interface Migration {
  id: number
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
  user_id: number
  config?: MigrationConfig
  error?: string
}

export interface MigrationConfig {
  source_connection: string
  target_project: string
  tables?: string[]
}

// API Key types
export interface APIKey {
  id: number
  name: string
  key: string
  is_active: boolean
  rate_limit: number
  created_at: string
}

// Stats types
export interface DashboardStats {
  total_migrations: number
  completed_migrations: number
  running_migrations: number
  failed_migrations: number
  success_rate: number
}

// API Response types
export interface APIResponse<T> {
  data: T
  message?: string
  success: boolean
}

// Login types
export interface LoginCredentials {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  user: User
}
