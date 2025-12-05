/**
 * API Service for communicating with the Go backend
 */

// In production (Railway), use relative URL since frontend is served by backend
// In development, use localhost
const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  // If running on Railway or production, use relative URL
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return '/api/v1'
  }
  return 'http://localhost:8080/api/v1'
}

const API_BASE_URL = getApiBaseUrl()

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

    let response: Response
    try {
      response = await fetch(`${this.baseUrl}${endpoint}`, config)
    } catch (networkError) {
      // Network error - server unreachable, CORS, etc.
      throw new Error('Unable to connect to server. Please check your internet connection and try again.')
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'An error occurred' }))
      throw new Error(error.error || `Request failed. Please try again.`)
    }

    // Handle empty responses
    const text = await response.text()
    return text ? JSON.parse(text) : (null as unknown as T)
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

  async forgotPassword(email: string) {
    return this.request<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: { email },
    })
  }

  async resetPassword(token: string, newPassword: string) {
    return this.request<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: { token, new_password: newPassword },
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
    use_windows_auth?: boolean
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

  // Migration files
  async getMigrationFiles(migrationId: number) {
    return this.request<{ files: { path: string; name: string; size: number; type: string }[] }>(`/migrations/${migrationId}/files`)
  }

  async getMigrationFileContent(migrationId: number, filepath: string) {
    return this.request<{ content: string }>(`/migrations/${migrationId}/files/${filepath}`)
  }

  getDownloadUrl(migrationId: number): string {
    return `${this.baseUrl}/migrations/${migrationId}/download`
  }

  // Stats
  async getDashboardStats() {
    return this.request<{
      total_migrations: number
      completed_migrations: number
      running_migrations: number
      failed_migrations: number
      success_rate: number
    }>('/stats')
  }

  // AI Support Chat
  async sendChatMessage(message: string, conversationHistory: { role: 'user' | 'assistant'; content: string }[], language: string = 'en') {
    return this.request<{ response: string; sources?: string[] }>('/chat', {
      method: 'POST',
      body: {
        message,
        history: conversationHistory,
        language
      },
    })
  }
}

// =============================================================================
// Python AI Service API (port 8081)
// =============================================================================

const AI_SERVICE_URL = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8081'

class AIServiceApi {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options

    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    }

    const config: RequestInit = {
      method,
      headers: requestHeaders,
    }

    if (body && method !== 'GET') {
      config.body = JSON.stringify(body)
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    const text = await response.text()
    return text ? JSON.parse(text) : (null as unknown as T)
  }

  // Validation endpoints
  async validateMigration(
    migrationId: number,
    options: {
      runDbtCompile?: boolean
      validateRowCounts?: boolean
      validateDataTypes?: boolean
      generateDbtTests?: boolean
      sourceConnection?: {
        host: string
        port?: number
        database: string
        username?: string
        password?: string
        useWindowsAuth?: boolean
      }
    } = {}
  ) {
    const {
      runDbtCompile = false,
      validateRowCounts = false,
      validateDataTypes = true,
      generateDbtTests = true,
      sourceConnection
    } = options

    const body: Record<string, unknown> = {
      run_dbt_compile: runDbtCompile,
      validate_row_counts: validateRowCounts,
      validate_data_types: validateDataTypes,
      generate_dbt_tests: generateDbtTests,
    }

    // Add source connection for row count validation
    if (sourceConnection) {
      body.source_host = sourceConnection.host
      body.source_port = sourceConnection.port || 1433
      body.source_database = sourceConnection.database
      body.source_username = sourceConnection.username || ''
      body.source_password = sourceConnection.password || ''
      body.use_windows_auth = sourceConnection.useWindowsAuth || false
    }

    return this.request<{
      migration_id: number
      project_path: string
      overall_status: string
      summary: {
        total_tables: number
        passed: number
        warnings: number
        failed: number
        pass_rate: number
        total_checks: number
        passed_checks: number
        warning_checks: number
        failed_checks: number
        check_pass_rate: number
        dbt_tests_generated: number
        row_count_validated: boolean
        syntax_validated: boolean
      }
      table_results: Array<{
        table_name: string
        source_table: string
        target_model: string
        overall_status: string
        checks: Array<{
          check_type: string
          name: string
          status: string
          details: string
          source_value?: any
          target_value?: any
          timestamp: string
        }>
      }>
      dbt_tests_generated: number
      row_count_validated: boolean
      syntax_validated: boolean
    }>(`/migrations/${migrationId}/validate`, {
      method: 'POST',
      body,
    })
  }

  async enhanceSchema(migrationId: number) {
    return this.request<{
      message: string
      path: string
      content: string
    }>(`/migrations/${migrationId}/enhance-schema`, {
      method: 'POST',
    })
  }

  // Get migration files from AI service
  async getMigrationFiles(migrationId: number) {
    return this.request<{
      migration_id: number
      project_path: string
      files: Array<{ path: string; name: string; size: number; type: string }>
    }>(`/migrations/${migrationId}/files`)
  }

  async getMigrationFileContent(migrationId: number, filepath: string) {
    return this.request<{ path: string; content: string; size: number }>(
      `/migrations/${migrationId}/files/${filepath}`
    )
  }

  // Warehouse Deployment endpoints
  async deployToWarehouse(
    migrationId: number,
    connection: {
      warehouse_type: 'snowflake' | 'bigquery' | 'databricks' | 'redshift' | 'fabric' | 'spark'
      // Snowflake
      account?: string
      warehouse?: string
      database?: string
      schema_name?: string
      username?: string
      password?: string
      role?: string
      // BigQuery
      project?: string
      dataset?: string
      keyfile?: string
      location?: string
      // Databricks
      host?: string
      http_path?: string
      token?: string
      catalog?: string
      // Redshift
      redshift_host?: string
      redshift_port?: number
      redshift_database?: string
      redshift_schema?: string
      redshift_username?: string
      redshift_password?: string
      // Microsoft Fabric
      fabric_server?: string
      fabric_port?: number
      fabric_database?: string
      fabric_schema?: string
      fabric_authentication?: 'sql' | 'serviceprincipal'
      fabric_username?: string
      fabric_password?: string
      fabric_tenant_id?: string
      fabric_client_id?: string
      fabric_client_secret?: string
      // Apache Spark
      spark_host?: string
      spark_port?: number
      spark_method?: 'thrift' | 'http' | 'session'
      spark_cluster?: string
      spark_token?: string
      spark_schema?: string
    },
    options: { run_tests?: boolean; full_refresh?: boolean } = {}
  ) {
    return this.request<{
      deployment_id: number
      status: string
      started_at: string
    }>(`/migrations/${migrationId}/deploy`, {
      method: 'POST',
      body: {
        connection,
        run_tests: options.run_tests ?? true,
        full_refresh: options.full_refresh ?? false
      }
    })
  }

  async getDeploymentStatus(migrationId: number, deploymentId: number) {
    return this.request<{
      deployment_id: number
      status: string
      dbt_run?: {
        success: boolean
        tables_created: number
        models_succeeded: number
        models_failed: number
        run_time_seconds: number
        error?: string
      }
      dbt_test?: {
        success: boolean
        tests_passed: number
        tests_failed: number
        tests_warned: number
        failed_tests: { test_name: string; location: string }[]
        error?: string
      }
      error?: string
      started_at: string
      completed_at?: string
    }>(`/migrations/${migrationId}/deployments/${deploymentId}`)
  }

  async listDeployments(migrationId: number) {
    return this.request<{
      migration_id: number
      deployments: Array<{
        deployment_id: number
        status: string
        started_at: string
        completed_at?: string
      }>
    }>(`/migrations/${migrationId}/deployments`)
  }

  // Data Quality Scanning
  async scanDataQuality(connection: {
    host: string
    port?: number
    database: string
    username?: string
    password?: string
    use_windows_auth?: boolean
    tables?: string[]
    sample_size?: number
  }) {
    return this.request<{
      database_name: string
      server: string
      tables_scanned: number
      total_rows_scanned: number
      total_issues: number
      critical_issues: number
      error_issues: number
      warning_issues: number
      info_issues: number
      overall_score: number
      scan_started_at: string
      scan_completed_at: string
      issues_by_severity: {
        critical: Array<{
          table_name: string
          column_name?: string
          category: string
          severity: string
          issue_type: string
          description: string
          affected_rows: number
          affected_percentage: number
          recommendation: string
        }>
        error: Array<any>
        warning: Array<any>
        info: Array<any>
      }
      tables: Array<{
        table_name: string
        schema_name: string
        row_count: number
        column_count: number
        columns: Array<{
          column_name: string
          data_type: string
          null_percentage: number
          distinct_count: number
        }>
        issues: Array<any>
      }>
    }>('/data-quality/scan', {
      method: 'POST',
      body: {
        host: connection.host,
        port: connection.port ?? 1433,
        database: connection.database,
        username: connection.username ?? '',
        password: connection.password ?? '',
        use_windows_auth: connection.use_windows_auth ?? false,
        tables: connection.tables,
        sample_size: connection.sample_size ?? 10000
      }
    })
  }
}

export const aiService = new AIServiceApi(AI_SERVICE_URL)

// Export singleton instance
export const api = new ApiService(API_BASE_URL)
export default api
