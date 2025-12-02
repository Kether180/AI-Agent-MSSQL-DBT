import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Migration } from '@/types'
import { api } from '@/services/api'

// Check if we're in demo mode (no backend)
const USE_DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'

// Mock migrations data for demo
const MOCK_MIGRATIONS: Migration[] = [
  {
    id: 1,
    name: 'ecommerce-production-v2',
    status: 'completed',
    progress: 100,
    source_database: 'ecommerce_prod',
    target_project: 'dbt_ecommerce',
    tables_count: 24,
    created_at: '2024-11-28T10:30:00Z',
    completed_at: '2024-11-28T11:45:00Z',
    user_id: 1
  },
  {
    id: 2,
    name: 'analytics-staging-migration',
    status: 'running',
    progress: 67,
    source_database: 'analytics_staging',
    target_project: 'dbt_analytics',
    tables_count: 18,
    created_at: '2024-12-01T08:00:00Z',
    user_id: 1
  },
  {
    id: 3,
    name: 'inventory-system-backup',
    status: 'pending',
    progress: 0,
    source_database: 'inventory_db',
    target_project: 'dbt_inventory',
    tables_count: 12,
    created_at: '2024-12-01T09:15:00Z',
    user_id: 1
  },
  {
    id: 4,
    name: 'legacy-crm-migration',
    status: 'failed',
    progress: 34,
    source_database: 'legacy_crm',
    target_project: 'dbt_crm',
    tables_count: 45,
    created_at: '2024-11-25T14:00:00Z',
    error: 'Connection timeout: Unable to reach source database after 30 seconds',
    user_id: 1
  },
  {
    id: 5,
    name: 'hr-system-v1',
    status: 'completed',
    progress: 100,
    source_database: 'hr_production',
    target_project: 'dbt_hr',
    tables_count: 8,
    created_at: '2024-11-20T16:30:00Z',
    completed_at: '2024-11-20T17:15:00Z',
    user_id: 1
  }
]

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
      if (USE_DEMO_MODE) {
        await new Promise(resolve => setTimeout(resolve, 500))
        const stored = localStorage.getItem('migrations')
        if (stored) {
          migrations.value = JSON.parse(stored)
        } else {
          migrations.value = [...MOCK_MIGRATIONS]
          localStorage.setItem('migrations', JSON.stringify(migrations.value))
        }

        // Simulate progress updates for running migrations
        migrations.value.forEach(m => {
          if (m.status === 'running' && m.progress < 100) {
            m.progress = Math.min(100, m.progress + Math.floor(Math.random() * 5))
            if (m.progress >= 100) {
              m.status = 'completed'
              m.completed_at = new Date().toISOString()
            }
          }
        })
        localStorage.setItem('migrations', JSON.stringify(migrations.value))
      } else {
        migrations.value = await api.getMigrations()
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch migrations'
    } finally {
      loading.value = false
    }
  }

  async function fetchMigration(id: number) {
    loading.value = true
    error.value = null

    try {
      if (USE_DEMO_MODE) {
        await new Promise(resolve => setTimeout(resolve, 300))
        const migration = migrations.value.find(m => m.id === id)
        if (migration) {
          currentMigration.value = migration
        } else {
          error.value = 'Migration not found'
        }
      } else {
        currentMigration.value = await api.getMigration(id)
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch migration'
    } finally {
      loading.value = false
    }
  }

  async function createMigration(data: {
    name: string
    source_database: string
    target_project: string
    tables?: string[]
    tables_count?: number
  }) {
    loading.value = true
    error.value = null

    try {
      if (USE_DEMO_MODE) {
        await new Promise(resolve => setTimeout(resolve, 1000))
        const newMigration: Migration = {
          id: Date.now(),
          name: data.name,
          status: 'pending',
          progress: 0,
          source_database: data.source_database,
          target_project: data.target_project,
          tables_count: data.tables_count || data.tables?.length || 0,
          created_at: new Date().toISOString(),
          user_id: 1
        }

        migrations.value.unshift(newMigration)
        localStorage.setItem('migrations', JSON.stringify(migrations.value))

        // Simulate starting the migration after 2 seconds
        setTimeout(() => {
          const m = migrations.value.find(migration => migration.id === newMigration.id)
          if (m) {
            m.status = 'running'
            localStorage.setItem('migrations', JSON.stringify(migrations.value))
          }
        }, 2000)

        return newMigration
      } else {
        const newMigration = await api.createMigration(data)
        migrations.value.unshift(newMigration)
        return newMigration
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to create migration'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteMigration(id: number) {
    try {
      if (USE_DEMO_MODE) {
        await new Promise(resolve => setTimeout(resolve, 300))
        migrations.value = migrations.value.filter((m) => m.id !== id)
        localStorage.setItem('migrations', JSON.stringify(migrations.value))
      } else {
        await api.deleteMigration(id)
        migrations.value = migrations.value.filter((m) => m.id !== id)
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to delete migration'
      throw err
    }
  }

  async function startMigration(id: number) {
    try {
      if (USE_DEMO_MODE) {
        const migration = migrations.value.find(m => m.id === id)
        if (migration && migration.status === 'pending') {
          migration.status = 'running'
          migration.progress = 0
          localStorage.setItem('migrations', JSON.stringify(migrations.value))

          // Simulate progress
          const interval = setInterval(() => {
            const m = migrations.value.find(mig => mig.id === id)
            if (m && m.status === 'running') {
              m.progress = Math.min(100, m.progress + Math.floor(Math.random() * 10) + 5)
              if (m.progress >= 100) {
                m.status = 'completed'
                m.completed_at = new Date().toISOString()
                clearInterval(interval)
              }
              localStorage.setItem('migrations', JSON.stringify(migrations.value))
            } else {
              clearInterval(interval)
            }
          }, 2000)
        }
      } else {
        await api.startMigration(id)
        const migration = migrations.value.find(m => m.id === id)
        if (migration) {
          migration.status = 'running'
          migration.progress = 0
        }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to start migration'
      throw err
    }
  }

  async function stopMigration(id: number) {
    try {
      if (USE_DEMO_MODE) {
        const migration = migrations.value.find(m => m.id === id)
        if (migration && migration.status === 'running') {
          migration.status = 'failed'
          migration.error = 'Migration stopped by user'
          localStorage.setItem('migrations', JSON.stringify(migrations.value))
        }
      } else {
        await api.stopMigration(id)
        const migration = migrations.value.find(m => m.id === id)
        if (migration) {
          migration.status = 'failed'
          migration.error = 'Migration stopped by user'
        }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to stop migration'
      throw err
    }
  }

  async function retryMigration(id: number) {
    const migration = migrations.value.find(m => m.id === id)
    if (migration && migration.status === 'failed') {
      migration.status = 'pending'
      migration.progress = 0
      migration.error = undefined
      if (USE_DEMO_MODE) {
        localStorage.setItem('migrations', JSON.stringify(migrations.value))
      }
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
    deleteMigration,
    startMigration,
    stopMigration,
    retryMigration
  }
})
