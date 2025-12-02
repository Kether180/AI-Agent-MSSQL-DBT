import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginCredentials, RegisterCredentials } from '@/types'
import { api } from '@/services/api'

// Check if we're in demo mode (no backend)
const USE_DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'

// Mock user for demo mode
const MOCK_USER: User = {
  id: 1,
  email: 'alex@datamigrate.ai',
  first_name: 'Alex',
  last_name: 'Demo',
  role: 'admin',
  is_admin: true,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  organization: {
    id: 1,
    name: 'Demo Company',
    slug: 'demo-company',
    plan: 'free',
    max_users: 5,
    max_migrations: 10,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
}

// Demo credentials
const DEMO_CREDENTIALS = {
  email: 'demo@datamigrate.ai',
  password: 'demo123'
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)
  const initialized = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  // Actions
  async function login(credentials: LoginCredentials) {
    loading.value = true
    error.value = null

    try {
      if (USE_DEMO_MODE) {
        // Demo mode: accept demo credentials or any valid-looking credentials
        await new Promise(resolve => setTimeout(resolve, 800))

        if (
          (credentials.email === DEMO_CREDENTIALS.email && credentials.password === DEMO_CREDENTIALS.password) ||
          (credentials.email && credentials.password && credentials.password.length >= 6)
        ) {
          const mockToken = 'mock_token_' + Date.now()
          token.value = mockToken
          user.value = { ...MOCK_USER, email: credentials.email }
          localStorage.setItem('access_token', mockToken)
          return true
        } else {
          error.value = 'Invalid credentials. Try demo@datamigrate.ai / demo123'
          return false
        }
      } else {
        // Real API call
        const response = await api.login(credentials.email, credentials.password)
        token.value = response.access_token
        user.value = response.user
        return true
      }
    } catch (err: any) {
      error.value = err.message || 'Login failed'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(credentials: RegisterCredentials) {
    loading.value = true
    error.value = null

    try {
      if (USE_DEMO_MODE) {
        // Demo mode: simulate registration
        await new Promise(resolve => setTimeout(resolve, 800))
        const mockToken = 'mock_token_' + Date.now()
        token.value = mockToken
        user.value = {
          ...MOCK_USER,
          email: credentials.email,
          first_name: credentials.first_name,
          last_name: credentials.last_name,
          organization: {
            ...MOCK_USER.organization!,
            name: credentials.organization_name
          }
        }
        localStorage.setItem('access_token', mockToken)
        return true
      } else {
        const response = await api.register(credentials)
        token.value = response.access_token
        user.value = response.user
        return true
      }
    } catch (err: any) {
      error.value = err.message || 'Registration failed'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      if (!USE_DEMO_MODE) {
        await api.logout()
      }
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('access_token')
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return

    try {
      if (USE_DEMO_MODE) {
        // In demo mode, restore user from token
        user.value = MOCK_USER
      } else {
        user.value = await api.getCurrentUser()
      }
    } catch (err) {
      // Token is invalid, clear it
      token.value = null
      user.value = null
      localStorage.removeItem('access_token')
    }
  }

  async function initialize() {
    if (initialized.value) return

    if (token.value) {
      await fetchCurrentUser()
    }
    initialized.value = true
  }

  return {
    user,
    token,
    loading,
    error,
    initialized,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    fetchCurrentUser,
    initialize
  }
})
