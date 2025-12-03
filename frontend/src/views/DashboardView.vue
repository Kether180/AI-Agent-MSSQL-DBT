<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMigrationsStore } from '@/stores/migrations'
import { api } from '@/services/api'
import type { DashboardStats } from '@/types'

const router = useRouter()
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
const userName = computed(() => {
  if (authStore.user?.first_name) return authStore.user.first_name
  return authStore.user?.email?.split('@')[0] || 'User'
})

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
    // Fetch stats and migrations in parallel
    const [statsResponse] = await Promise.all([
      api.getDashboardStats().catch(() => null),
      migrationsStore.fetchMigrations()
    ])

    // Use API stats if available, otherwise compute from migrations
    if (statsResponse) {
      stats.value = statsResponse
    } else {
      // Fallback: compute stats from migrations
      const migrations = migrationsStore.migrations
      stats.value = {
        total_migrations: migrations.length,
        completed_migrations: migrations.filter(m => m.status === 'completed').length,
        running_migrations: migrations.filter(m => m.status === 'running').length,
        failed_migrations: migrations.filter(m => m.status === 'failed').length,
        success_rate: migrations.length > 0
          ? Math.round((migrations.filter(m => m.status === 'completed').length / migrations.length) * 100)
          : 0
      }
    }

    recentMigrations.value = migrationsStore.migrations.slice(0, 5)
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    isLoading.value = false
  }
}

const getStatusBadge = (status: string): { class: string; text: string } => {
  const badges: Record<string, { class: string; text: string }> = {
    completed: { class: 'bg-green-100 text-green-800', text: 'Completed' },
    running: { class: 'bg-blue-100 text-blue-800', text: 'Running' },
    failed: { class: 'bg-red-100 text-red-800', text: 'Failed' },
    pending: { class: 'bg-yellow-100 text-yellow-800', text: 'Pending' }
  }
  return badges[status] ?? badges.pending!
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

const goToMigration = (id: number) => {
  router.push(`/migrations/${id}`)
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
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-indigo-50">
    <!-- Header with gradient -->
    <div class="bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 shadow-lg">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-8">
          <h1 class="text-3xl font-bold text-white animate-fade-in">
            Welcome back, {{ userName }}!
          </h1>
          <p class="mt-2 text-indigo-100">
            Here's what's happening with your migrations today.
          </p>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <!-- Stats Grid with enhanced cards -->
      <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <!-- Total Migrations -->
        <div class="stat-card bg-gradient-to-br from-white to-gray-50 overflow-hidden shadow-md rounded-xl border border-gray-100 hover:shadow-xl hover:scale-105 transition-all duration-300">
          <div class="p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-3 shadow-lg">
                <svg class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">
                    Total Migrations
                  </dt>
                  <dd>
                    <div class="text-3xl font-bold text-gray-900 mt-1">
                      {{ isLoading ? '...' : stats.total_migrations }}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="h-1 bg-gradient-to-r from-indigo-500 to-purple-500"></div>
        </div>

        <!-- Completed -->
        <div class="stat-card bg-gradient-to-br from-white to-green-50 overflow-hidden shadow-md rounded-xl border border-gray-100 hover:shadow-xl hover:scale-105 transition-all duration-300">
          <div class="p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl p-3 shadow-lg">
                <svg class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">
                    Completed
                  </dt>
                  <dd>
                    <div class="text-3xl font-bold text-green-600 mt-1">
                      {{ isLoading ? '...' : stats.completed_migrations }}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="h-1 bg-gradient-to-r from-green-500 to-emerald-500"></div>
        </div>

        <!-- Running -->
        <div class="stat-card bg-gradient-to-br from-white to-blue-50 overflow-hidden shadow-md rounded-xl border border-gray-100 hover:shadow-xl hover:scale-105 transition-all duration-300">
          <div class="p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl p-3 shadow-lg">
                <svg class="h-7 w-7 text-white animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">
                    Running
                  </dt>
                  <dd>
                    <div class="text-3xl font-bold text-blue-600 mt-1">
                      {{ isLoading ? '...' : stats.running_migrations }}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="h-1 bg-gradient-to-r from-blue-500 to-cyan-500"></div>
        </div>

        <!-- Success Rate -->
        <div class="stat-card bg-gradient-to-br from-white to-purple-50 overflow-hidden shadow-md rounded-xl border border-gray-100 hover:shadow-xl hover:scale-105 transition-all duration-300">
          <div class="p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl p-3 shadow-lg">
                <svg class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">
                    Success Rate
                  </dt>
                  <dd>
                    <div :class="['text-3xl font-bold mt-1', successRateColor]">
                      {{ isLoading ? '...' : stats.success_rate + '%' }}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="h-1 bg-gradient-to-r from-purple-500 to-pink-500"></div>
        </div>
      </div>

      <!-- Recent Migrations -->
      <div class="mt-8">
        <div class="bg-white shadow-lg rounded-xl border border-gray-100 overflow-hidden">
          <div class="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg p-2 mr-3">
                  <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
                <h3 class="text-lg font-semibold text-gray-900">
                  Recent Migrations
                </h3>
              </div>
              <router-link
                to="/migrations"
                class="inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-500 transition-colors"
              >
                View all
                <svg class="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </router-link>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="isLoading" class="px-6 py-16 text-center">
            <div class="relative">
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="h-16 w-16 rounded-full border-4 border-indigo-100"></div>
              </div>
              <svg class="animate-spin h-16 w-16 mx-auto text-indigo-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
            </div>
            <p class="mt-4 text-sm text-gray-500 font-medium">Loading migrations...</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="recentMigrations.length === 0" class="px-6 py-16 text-center">
            <div class="mx-auto h-20 w-20 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
              <svg class="h-10 w-10 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
              </svg>
            </div>
            <h3 class="mt-4 text-lg font-semibold text-gray-900">No migrations yet</h3>
            <p class="mt-2 text-sm text-gray-500">Get started by creating your first migration.</p>
            <div class="mt-6">
              <router-link
                to="/migrations/new"
                class="inline-flex items-center px-5 py-2.5 border border-transparent shadow-md text-sm font-medium rounded-lg text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 hover:shadow-lg"
              >
                <svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                Create Migration
              </router-link>
            </div>
          </div>

          <!-- Migrations List -->
          <ul v-else role="list" class="divide-y divide-gray-100">
            <li
              v-for="migration in recentMigrations"
              :key="migration.id"
              @click="goToMigration(migration.id)"
              class="px-6 py-4 hover:bg-gradient-to-r hover:from-indigo-50 hover:to-transparent cursor-pointer transition-all duration-200 group"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1 min-w-0">
                  <h4 class="text-sm font-semibold text-gray-900 group-hover:text-indigo-600 truncate transition-colors">
                    {{ migration.name }}
                  </h4>
                  <p class="mt-1 text-sm text-gray-500">
                    Created {{ formatDate(migration.created_at) }}
                  </p>
                </div>
                <div class="ml-4 flex-shrink-0 flex items-center">
                  <span
                    :class="[
                      'inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold shadow-sm',
                      getStatusBadge(migration.status).class
                    ]"
                  >
                    {{ getStatusBadge(migration.status).text }}
                  </span>
                  <svg class="ml-3 h-5 w-5 text-gray-400 group-hover:text-indigo-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                  </svg>
                </div>
              </div>

              <!-- Progress Bar (if running) -->
              <div v-if="migration.status === 'running' && migration.progress" class="mt-3">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs font-medium text-blue-600">In Progress</span>
                  <span class="text-xs font-semibold text-blue-600">{{ migration.progress }}%</span>
                </div>
                <div class="w-full bg-blue-100 rounded-full h-2 overflow-hidden">
                  <div
                    class="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full transition-all duration-500 ease-out"
                    :style="{ width: `${migration.progress}%` }"
                  />
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="mt-8">
        <div class="flex items-center mb-5">
          <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg p-2 mr-3">
            <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900">Quick Actions</h3>
        </div>
        <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <router-link
            to="/migrations/new"
            class="action-card bg-gradient-to-br from-white to-indigo-50 overflow-hidden shadow-md rounded-xl border border-gray-100 hover:shadow-xl hover:scale-105 transition-all duration-300 group"
          >
            <div class="p-6">
              <div class="flex items-center">
                <div class="flex-shrink-0 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-3 shadow-lg group-hover:shadow-indigo-200">
                  <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                  </svg>
                </div>
                <div class="ml-4">
                  <h3 class="text-lg font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">New Migration</h3>
                  <p class="mt-1 text-sm text-gray-500">Start a new database migration</p>
                </div>
              </div>
            </div>
            <div class="h-1 bg-gradient-to-r from-indigo-500 to-purple-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>
          </router-link>

          <router-link
            to="/migrations"
            class="action-card bg-gradient-to-br from-white to-green-50 overflow-hidden shadow-md rounded-xl border border-gray-100 hover:shadow-xl hover:scale-105 transition-all duration-300 group"
          >
            <div class="p-6">
              <div class="flex items-center">
                <div class="flex-shrink-0 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl p-3 shadow-lg group-hover:shadow-green-200">
                  <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                  </svg>
                </div>
                <div class="ml-4">
                  <h3 class="text-lg font-semibold text-gray-900 group-hover:text-green-600 transition-colors">View All</h3>
                  <p class="mt-1 text-sm text-gray-500">Browse all migrations</p>
                </div>
              </div>
            </div>
            <div class="h-1 bg-gradient-to-r from-green-500 to-emerald-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>
          </router-link>

          <router-link
            to="/docs"
            class="action-card bg-gradient-to-br from-white to-purple-50 overflow-hidden shadow-md rounded-xl border border-gray-100 hover:shadow-xl hover:scale-105 transition-all duration-300 group"
          >
            <div class="p-6">
              <div class="flex items-center">
                <div class="flex-shrink-0 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl p-3 shadow-lg group-hover:shadow-purple-200">
                  <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                  </svg>
                </div>
                <div class="ml-4">
                  <h3 class="text-lg font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">Documentation</h3>
                  <p class="mt-1 text-sm text-gray-500">Learn how to use DataMigrate AI</p>
                </div>
              </div>
            </div>
            <div class="h-1 bg-gradient-to-r from-purple-500 to-pink-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>
          </router-link>

          <router-link
            to="/settings"
            class="action-card bg-gradient-to-br from-white to-gray-50 overflow-hidden shadow-md rounded-xl border border-gray-100 hover:shadow-xl hover:scale-105 transition-all duration-300 group"
          >
            <div class="p-6">
              <div class="flex items-center">
                <div class="flex-shrink-0 bg-gradient-to-br from-gray-600 to-gray-700 rounded-xl p-3 shadow-lg group-hover:shadow-gray-300">
                  <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                </div>
                <div class="ml-4">
                  <h3 class="text-lg font-semibold text-gray-900 group-hover:text-gray-700 transition-colors">Settings</h3>
                  <p class="mt-1 text-sm text-gray-500">Manage connections & API keys</p>
                </div>
              </div>
            </div>
            <div class="h-1 bg-gradient-to-r from-gray-500 to-gray-600 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom animations */
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.5s ease-out;
}

/* Stat card hover glow effect */
.stat-card:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

/* Action card styles */
.action-card {
  position: relative;
}

.action-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 0.75rem;
  padding: 1px;
  background: linear-gradient(135deg, transparent 0%, rgba(99, 102, 241, 0.1) 100%);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
</style>
