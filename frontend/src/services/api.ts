/**
 * API Service for communicating with the Go backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1'

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  body?: unknown
  headers?: Record<string, string>
}

class ApiService {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
    // Load token from localStorage on init
    this.token = localStorage.getItem('access_token')
  }

  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem('access_token', token)
    } else {
      localStorage.removeItem('access_token')
    }
  }

  getToken(): string | null {
    return this.token
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options

    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    }

    if (this.token) {
      requestHeaders['Authorization'] = `Bearer ${this.token}`
    }

    const config: RequestInit = {
      method,
      headers: requestHeaders,
      credentials: 'include',
    }

    if (body && method !== 'GET') {
      config.body = JSON.stringify(body)
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'An error occurred' }))
      throw new Error(error.error || `HTTP error! status: ${response.status}`)
    }

    // Handle empty responses
    const text = await response.text()
    return text ? JSON.parse(text) : null
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.request<{ access_token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    this.setToken(response.access_token)
    return response
  }

  async register(credentials: {
    email: string
    password: string
    first_name: string
    last_name: string
    organization_name: string
    job_title?: string
    phone?: string
  }) {
    const response = await this.request<{ access_token: string; user: any }>('/auth/register', {
      method: 'POST',
      body: credentials,
    })
    this.setToken(response.access_token)
    return response
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' })
    } finally {
      this.setToken(null)
    }
  }

  async getCurrentUser() {
    return this.request<any>('/auth/me')
  }

  async updateProfile(data: {
    first_name?: string
    last_name?: string
    email?: string
    job_title?: string
    phone?: string
  }) {
    return this.request<any>('/auth/profile', {
      method: 'PUT',
      body: data,
    })
  }

  async changePassword(data: {
    current_password: string
    new_password: string
  }) {
    return this.request<{ message: string }>('/auth/password', {
      method: 'PUT',
      body: data,
    })
  }

  // Migrations endpoints
  async getMigrations() {
    return this.request<any[]>('/migrations')
  }

  async getMigration(id: number) {
    return this.request<any>(`/migrations/${id}`)
  }

  async createMigration(data: {
    name: string
    source_database: string
    target_project: string
    tables?: string[]
    include_views?: boolean
  }) {
    return this.request<any>('/migrations', {
      method: 'POST',
      body: data,
    })
  }

  async deleteMigration(id: number) {
    return this.request<{ message: string }>(`/migrations/${id}`, {
      method: 'DELETE',
    })
  }

  async startMigration(id: number) {
    return this.request<{ message: string }>(`/migrations/${id}/start`, {
      method: 'POST',
    })
  }

  async stopMigration(id: number) {
    return this.request<{ message: string }>(`/migrations/${id}/stop`, {
      method: 'POST',
    })
  }

  // Stats
  async getStats() {
    return this.request<{
      total_migrations: number
      completed_migrations: number
      running_migrations: number
      failed_migrations: number
      success_rate: number
    }>('/stats')
  }

  // Database connections
  async getConnections() {
    return this.request<any[]>('/connections')
  }

  async getConnection(id: number) {
    return this.request<any>(`/connections/${id}`)
  }

  async createConnection(data: {
    name: string
    db_type: string
    host: string
    port: number
    database_name: string
    username: string
    password: string
    is_source?: boolean
  }) {
    return this.request<any>('/connections', {
      method: 'POST',
      body: data,
    })
  }

  async updateConnection(id: number, data: any) {
    return this.request<any>(`/connections/${id}`, {
      method: 'PUT',
      body: data,
    })
  }

  async deleteConnection(id: number) {
    return this.request<{ message: string }>(`/connections/${id}`, {
      method: 'DELETE',
    })
  }

  async testConnection(id: number) {
    return this.request<{ success: boolean; message: string }>(`/connections/${id}/test`, {
      method: 'POST',
    })
  }

  // API Keys
  async getApiKeys() {
    return this.request<any[]>('/api-keys')
  }

  async createApiKey(data: { name: string; rate_limit?: number }) {
    return this.request<{ id: number; name: string; key: string; rate_limit: number; message: string }>(
      '/api-keys',
      {
        method: 'POST',
        body: data,
      }
    )
  }

  async deleteApiKey(id: number) {
    return this.request<{ message: string }>(`/api-keys/${id}`, {
      method: 'DELETE',
    })
  }

  async toggleApiKey(id: number) {
    return this.request<{ message: string; is_active: boolean }>(`/api-keys/${id}/toggle`, {
      method: 'PUT',
    })
  }
}

// Export singleton instance
export const api = new ApiService(API_BASE_URL)
export default api
