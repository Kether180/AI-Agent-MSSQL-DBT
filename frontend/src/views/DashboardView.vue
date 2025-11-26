<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMigrationsStore } from '@/stores/migrations'
import type { DashboardStats } from '@/types'

const authStore = useAuthStore()
const migrationsStore = useMigrationsStore()

const stats = ref<DashboardStats>({
  total_migrations: 0,
  completed_migrations: 0,
  running_migrations: 0,
  failed_migrations: 0,
  success_rate: 0
})

const isLoading = ref(true)
const recentMigrations = ref<any[]>([])

// Computed
const userName = computed(() => authStore.user?.email?.split('@')[0] || 'User')

const successRateColor = computed(() => {
  const rate = stats.value.success_rate
  if (rate >= 90) return 'text-green-600'
  if (rate >= 70) return 'text-yellow-600'
  return 'text-red-600'
})

// Methods
const fetchDashboardData = async () => {
  isLoading.value = true
  try {
    // Fetch stats from API
    // const response = await api.get('/api/v1/stats')
    // stats.value = response.data

    // Fetch recent migrations
    await migrationsStore.fetchMigrations()
    recentMigrations.value = migrationsStore.migrations.slice(0, 5)

    // Mock stats for now (replace with API call)
    stats.value = {
      total_migrations: migrationsStore.migrations.length,
      completed_migrations: migrationsStore.migrations.filter(m => m.status === 'completed').length,
      running_migrations: migrationsStore.migrations.filter(m => m.status === 'running').length,
      failed_migrations: migrationsStore.migrations.filter(m => m.status === 'failed').length,
      success_rate: Math.round((migrationsStore.migrations.filter(m => m.status === 'completed').length / migrationsStore.migrations.length) * 100) || 0
    }
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    isLoading.value = false
  }
}

const getStatusBadge = (status: string) => {
  const badges: Record<string, { class: string; text: string }> = {
    completed: { class: 'bg-green-100 text-green-800', text: 'Completed' },
    running: { class: 'bg-blue-100 text-blue-800', text: 'Running' },
    failed: { class: 'bg-red-100 text-red-800', text: 'Failed' },
    pending: { class: 'bg-yellow-100 text-yellow-800', text: 'Pending' }
  }
  return badges[status] || badges.pending
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  fetchDashboardData()

  // Refresh stats every 30 seconds
  const interval = setInterval(fetchDashboardData, 30000)

  // Cleanup
  return () => clearInterval(interval)
})
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <h1 class="text-3xl font-bold text-gray-900">
            Welcome back, {{ userName }}! 👋
          </h1>
          <p class="mt-1 text-sm text-gray-500">
            Here's what's happening with your migrations today.
          </p>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <!-- Stats Grid -->
      <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <!-- Total Migrations -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">
                    Total Migrations
                  </dt>
                  <dd>
                    <div class="text-lg font-medium text-gray-900">
                      {{ isLoading ? '...' : stats.total_migrations }}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <!-- Completed -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">
                    Completed
                  </dt>
                  <dd>
                    <div class="text-lg font-medium text-gray-900">
                      {{ isLoading ? '...' : stats.completed_migrations }}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <!-- Running -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-blue-400 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">
                    Running
                  </dt>
                  <dd>
                    <div class="text-lg font-medium text-gray-900">
                      {{ isLoading ? '...' : stats.running_migrations }}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <!-- Success Rate -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">
                    Success Rate
                  </dt>
                  <dd>
                    <div :class="['text-lg font-medium', successRateColor]">
                      {{ isLoading ? '...' : stats.success_rate + '%' }}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Migrations -->
      <div class="mt-8">
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-medium leading-6 text-gray-900">
                Recent Migrations
              </h3>
              <router-link
                to="/migrations"
                class="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View all
              </router-link>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="isLoading" class="px-4 py-12 text-center">
            <svg class="animate-spin h-8 w-8 mx-auto text-indigo-600" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
            <p class="mt-2 text-sm text-gray-500">Loading migrations...</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="recentMigrations.length === 0" class="px-4 py-12 text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No migrations yet</h3>
            <p class="mt-1 text-sm text-gray-500">Get started by creating a new migration.</p>
            <div class="mt-6">
              <router-link
                to="/migrations/new"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
              >
                Create Migration
              </router-link>
            </div>
          </div>

          <!-- Migrations List -->
          <ul v-else role="list" class="divide-y divide-gray-200">
            <li v-for="migration in recentMigrations" :key="migration.id" class="px-4 py-4 sm:px-6 hover:bg-gray-50 cursor-pointer">
              <div class="flex items-center justify-between">
                <div class="flex-1 min-w-0">
                  <h4 class="text-sm font-medium text-indigo-600 truncate">
                    {{ migration.name }}
                  </h4>
                  <p class="mt-1 text-sm text-gray-500">
                    Created {{ formatDate(migration.created_at) }}
                  </p>
                </div>
                <div class="ml-4 flex-shrink-0">
                  <span
                    :class="[
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      getStatusBadge(migration.status).class
                    ]"
                  >
                    {{ getStatusBadge(migration.status).text }}
                  </span>
                </div>
              </div>

              <!-- Progress Bar (if running) -->
              <div v-if="migration.status === 'running' && migration.progress" class="mt-2">
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    :style="{ width: `${migration.progress}%` }"
                  />
                </div>
                <p class="mt-1 text-xs text-gray-500">
                  {{ migration.progress }}% complete
                </p>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <router-link
          to="/migrations/new"
          class="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
        >
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0 bg-indigo-500 rounded-md p-3">
                <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
              </div>
              <div class="ml-5">
                <h3 class="text-lg font-medium text-gray-900">New Migration</h3>
                <p class="mt-1 text-sm text-gray-500">Start a new database migration</p>
              </div>
            </div>
          </div>
        </router-link>

        <router-link
          to="/migrations"
          class="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
        >
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0 bg-green-500 rounded-md p-3">
                <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
              </div>
              <div class="ml-5">
                <h3 class="text-lg font-medium text-gray-900">View All</h3>
                <p class="mt-1 text-sm text-gray-500">Browse all migrations</p>
              </div>
            </div>
          </div>
        </router-link>

        <a
          href="https://docs.getdbt.com/"
          target="_blank"
          class="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
        >
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0 bg-purple-500 rounded-md p-3">
                <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
              </div>
              <div class="ml-5">
                <h3 class="text-lg font-medium text-gray-900">Documentation</h3>
                <p class="mt-1 text-sm text-gray-500">Learn about dbt migrations</p>
              </div>
            </div>
          </div>
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional custom styles if needed */
</style>
