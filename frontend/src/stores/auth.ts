import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api/client'
import type { User, LoginCredentials } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  // Actions
  async function login(credentials: LoginCredentials) {
    loading.value = true
    error.value = null

    try {
      const response = await authAPI.login(credentials)
      token.value = response.data.access_token
      user.value = response.data.user
      localStorage.setItem('access_token', token.value)
      return true
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Login failed'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authAPI.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('access_token')
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return

    try {
      const response = await authAPI.getCurrentUser()
      user.value = response.data
    } catch (err) {
      // Token invalid, logout
      await logout()
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    fetchCurrentUser
  }
})
