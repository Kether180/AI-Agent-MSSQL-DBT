import { defineStore } from 'pinia'
import { ref } from 'vue'
import { migrationsAPI } from '@/api/client'
import type { Migration } from '@/types'

export const useMigrationsStore = defineStore('migrations', () => {
  // State
  const migrations = ref<Migration[]>([])
  const currentMigration = ref<Migration | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchMigrations() {
    loading.value = true
    error.value = null

    try {
      const response = await migrationsAPI.getAll()
      migrations.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch migrations'
    } finally {
      loading.value = false
    }
  }

  async function fetchMigration(id: number) {
    loading.value = true
    error.value = null

    try {
      const response = await migrationsAPI.getOne(id)
      currentMigration.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch migration'
    } finally {
      loading.value = false
    }
  }

  async function createMigration(data: Partial<Migration>) {
    loading.value = true
    error.value = null

    try {
      const response = await migrationsAPI.create(data)
      migrations.value.unshift(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to create migration'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteMigration(id: number) {
    try {
      await migrationsAPI.delete(id)
      migrations.value = migrations.value.filter((m) => m.id !== id)
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to delete migration'
      throw err
    }
  }

  return {
    migrations,
    currentMigration,
    loading,
    error,
    fetchMigrations,
    fetchMigration,
    createMigration,
    deleteMigration
  }
})
