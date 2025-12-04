// Organization types
export interface Organization {
  id: number
  name: string
  slug: string
  plan: 'free' | 'starter' | 'professional' | 'enterprise'
  max_users: number
  max_migrations: number
  created_at: string
  updated_at: string
}

// User types
export interface User {
  id: number
  email: string
  first_name?: string
  last_name?: string
  job_title?: string
  phone?: string
  organization_id?: number
  role: 'admin' | 'member' | 'viewer'
  is_admin: boolean
  is_active: boolean
  last_login_at?: string
  created_at: string
  updated_at: string
  organization?: Organization
}

// Registration types
export interface RegisterCredentials {
  email: string
  password: string
  first_name: string
  last_name: string
  organization_name: string
  job_title?: string
  phone?: string
}

// Migration types
export interface Migration {
  id: number
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  source_database: string
  target_project: string
  tables_count: number
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

// Database Connection types
export interface DatabaseConnection {
  id: number
  name: string
  db_type: string
  host: string
  port: number
  database_name: string
  username: string
  is_source: boolean
  user_id: number
  created_at: string
  updated_at: string
  // Local UI state
  status?: 'connected' | 'disconnected' | 'testing' | 'error'
}

export interface CreateConnectionRequest {
  name: string
  db_type: string
  host: string
  port: number
  database_name: string
  username: string
  password: string
  use_windows_auth?: boolean
  is_source?: boolean
}

// API Key types
export interface APIKey {
  id: number
  name: string
  key?: string
  is_active: boolean
  rate_limit: number
  created_at: string
  last_used_at?: string
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
