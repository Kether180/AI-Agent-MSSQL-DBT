import axios, { type AxiosInstance } from 'axios'
import type {
  User,
  Migration,
  APIKey,
  DashboardStats,
  LoginCredentials,
  LoginResponse
} from '@/types'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API methods
export const authAPI = {
  login: (credentials: LoginCredentials) =>
    api.post<LoginResponse>('/auth/login', credentials),

  logout: () => api.post('/auth/logout'),

  getCurrentUser: () => api.get<User>('/auth/me')
}

export const migrationsAPI = {
  getAll: () => api.get<Migration[]>('/migrations'),

  getOne: (id: number) => api.get<Migration>(`/migrations/${id}`),

  create: (data: Partial<Migration>) => api.post<Migration>('/migrations', data),

  delete: (id: number) => api.delete(`/migrations/${id}`),

  getProgress: (id: number) => api.get<{ progress: number }>(`/migrations/${id}/progress`)
}

export const statsAPI = {
  getDashboard: () => api.get<DashboardStats>('/stats/dashboard')
}

export const apiKeysAPI = {
  getAll: () => api.get<APIKey[]>('/api-keys'),

  create: (name: string) => api.post<APIKey>('/api-keys', { name }),

  revoke: (id: number) => api.delete(`/api-keys/${id}`)
}

export default api
