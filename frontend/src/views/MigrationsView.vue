<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMigrationsStore } from '@/stores/migrations'
import type { Migration } from '@/types'

const router = useRouter()
const migrationsStore = useMigrationsStore()

const searchQuery = ref('')
const filterStatus = ref('all')
const isLoading = ref(false)

// Computed
const filteredMigrations = computed(() => {
  let filtered = migrationsStore.migrations

  // Filter by status
  if (filterStatus.value !== 'all') {
    filtered = filtered.filter(m => m.status === filterStatus.value)
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(m =>
      m.name.toLowerCase().includes(query)
    )
  }

  return filtered
})

const statusCounts = computed(() => {
  const migrations = migrationsStore.migrations
  return {
    all: migrations.length,
    pending: migrations.filter(m => m.status === 'pending').length,
    running: migrations.filter(m => m.status === 'running').length,
    completed: migrations.filter(m => m.status === 'completed').length,
    failed: migrations.filter(m => m.status === 'failed').length
  }
})

// Methods
const fetchMigrations = async () => {
  isLoading.value = true
  try {
    await migrationsStore.fetchMigrations()
  } catch (error) {
    console.error('Failed to fetch migrations:', error)
  } finally {
    isLoading.value = false
  }
}

const viewMigration = (migration: Migration) => {
  router.push(`/migrations/${migration.id}`)
}

const createNewMigration = () => {
  router.push('/migrations/new')
}

const deleteMigration = async (id: number) => {
  if (!confirm('Are you sure you want to delete this migration?')) {
    return
  }

  try {
    await migrationsStore.deleteMigration(id)
    await fetchMigrations()
  } catch (error) {
    console.error('Failed to delete migration:', error)
    alert('Failed to delete migration')
  }
}

const getStatusBadge = (status: string): { class: string; text: string; icon: string; gradient: string; pulse?: boolean } => {
  const badges: Record<string, { class: string; text: string; icon: string; gradient: string; pulse?: boolean }> = {
    completed: {
      class: 'bg-gradient-to-r from-emerald-100 to-green-100 text-emerald-800 border border-emerald-200',
      text: 'Completed',
      icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
      gradient: 'from-emerald-500 to-green-500'
    },
    running: {
      class: 'bg-gradient-to-r from-blue-100 to-cyan-100 text-blue-800 border border-blue-200',
      text: 'Running',
      icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
      gradient: 'from-blue-500 to-cyan-500',
      pulse: true
    },
    failed: {
      class: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-800 border border-red-200',
      text: 'Failed',
      icon: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
      gradient: 'from-red-500 to-rose-500'
    },
    pending: {
      class: 'bg-gradient-to-r from-amber-100 to-yellow-100 text-amber-800 border border-amber-200',
      text: 'Pending',
      icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
      gradient: 'from-amber-400 to-yellow-500'
    }
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

const getTimeSince = (dateString: string) => {
  const seconds = Math.floor((new Date().getTime() - new Date(dateString).getTime()) / 1000)

  let interval = seconds / 31536000
  if (interval > 1) return Math.floor(interval) + ' years ago'

  interval = seconds / 2592000
  if (interval > 1) return Math.floor(interval) + ' months ago'

  interval = seconds / 86400
  if (interval > 1) return Math.floor(interval) + ' days ago'

  interval = seconds / 3600
  if (interval > 1) return Math.floor(interval) + ' hours ago'

  interval = seconds / 60
  if (interval > 1) return Math.floor(interval) + ' minutes ago'

  return 'Just now'
}

// Lifecycle
onMounted(() => {
  fetchMigrations()

  // Refresh every 10 seconds
  const interval = setInterval(fetchMigrations, 10000)

  return () => clearInterval(interval)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/30">
    <!-- Top Header Bar - Sticky -->
    <div class="border-b border-gray-200 bg-white/80 backdrop-blur-xl sticky top-0 z-30 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center space-x-3">
            <div class="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-xl p-2 shadow-lg shadow-cyan-500/25">
              <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"/>
              </svg>
            </div>
            <div>
              <h1 class="text-lg font-bold text-slate-800">Migrations</h1>
              <p class="text-xs text-slate-500">Manage your MSSQL to dbt migrations</p>
            </div>
          </div>
          <button
            @click="createNewMigration"
            class="inline-flex items-center px-4 py-2 text-sm font-medium rounded-xl text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 shadow-lg shadow-cyan-500/25 hover:shadow-xl transition-all duration-200"
          >
            <svg class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            New Migration
          </button>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <div class="max-w-7xl mx-auto">
      <!-- Filters -->
      <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-slate-200/50 p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Search -->
          <div>
            <label for="search" class="block text-sm font-semibold text-gray-700 mb-2">
              Search
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </div>
              <input
                id="search"
                v-model="searchQuery"
                type="text"
                placeholder="Search by name..."
                class="block w-full pl-11 pr-4 py-2.5 border border-gray-200 rounded-xl leading-5 bg-gray-50 placeholder-gray-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition-all duration-200"
              />
            </div>
          </div>

          <!-- Status Filter -->
          <div>
            <label for="status" class="block text-sm font-semibold text-gray-700 mb-2">
              Status
            </label>
            <select
              id="status"
              v-model="filterStatus"
              class="block w-full pl-4 pr-10 py-2.5 text-base border border-gray-200 bg-gray-50 focus:outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm rounded-xl transition-all duration-200"
            >
              <option value="all">All ({{ statusCounts.all }})</option>
              <option value="pending">Pending ({{ statusCounts.pending }})</option>
              <option value="running">Running ({{ statusCounts.running }})</option>
              <option value="completed">Completed ({{ statusCounts.completed }})</option>
              <option value="failed">Failed ({{ statusCounts.failed }})</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-slate-200/50 p-16 text-center">
        <div class="relative">
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="h-16 w-16 rounded-full border-4 border-cyan-100"></div>
          </div>
          <svg class="animate-spin h-16 w-16 mx-auto text-cyan-600" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
          </svg>
        </div>
        <p class="mt-6 text-gray-500 font-medium">Loading migrations...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredMigrations.length === 0" class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-slate-200/50 p-16 text-center">
        <div class="mx-auto h-24 w-24 rounded-full bg-gradient-to-br from-cyan-100 to-teal-100 flex items-center justify-center">
          <svg class="h-12 w-12 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
          </svg>
        </div>
        <h3 class="mt-6 text-xl font-semibold text-gray-900">No migrations found</h3>
        <p class="mt-2 text-sm text-gray-500">
          {{ searchQuery || filterStatus !== 'all' ? 'Try adjusting your filters' : 'Get started by creating a new migration' }}
        </p>
        <div class="mt-8">
          <button
            @click="createNewMigration"
            class="inline-flex items-center px-6 py-3 border border-transparent shadow-lg text-sm font-medium rounded-xl text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 transition-all duration-200 hover:shadow-xl hover:scale-105"
          >
            <svg class="mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Create Migration
          </button>
        </div>
      </div>

      <!-- Migrations Grid -->
      <div v-else class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="migration in filteredMigrations"
          :key="migration.id"
          class="migration-card bg-white/80 backdrop-blur-sm overflow-hidden shadow-lg rounded-2xl border border-slate-200/50 hover:shadow-xl hover:scale-[1.02] transition-all duration-300 cursor-pointer group"
          @click="viewMigration(migration)"
        >
          <!-- Status gradient bar at top -->
          <div :class="['h-1.5 bg-gradient-to-r', getStatusBadge(migration.status).gradient]"></div>

          <div class="p-6">
            <!-- Header -->
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900 group-hover:text-cyan-600 truncate transition-colors">
                {{ migration.name }}
              </h3>
              <span
                :class="[
                  'inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold shadow-sm',
                  getStatusBadge(migration.status).class
                ]"
              >
                <svg :class="['w-3.5 h-3.5 mr-1.5', getStatusBadge(migration.status).pulse ? 'animate-spin' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getStatusBadge(migration.status).icon"/>
                </svg>
                {{ getStatusBadge(migration.status).text }}
              </span>
            </div>

            <!-- Pending State Call-to-Action -->
            <div v-if="migration.status === 'pending'" class="mb-4 p-3 bg-gradient-to-r from-amber-50 to-yellow-50 rounded-lg border border-amber-200">
              <div class="flex items-center">
                <div class="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center mr-3 shadow-sm">
                  <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-semibold text-amber-800">Ready to Start</p>
                  <p class="text-xs text-amber-600">Click to view details and start migration</p>
                </div>
              </div>
            </div>

            <!-- Progress (if running) -->
            <div v-if="migration.status === 'running'" class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-semibold text-blue-600">In Progress</span>
                <span class="text-sm font-bold text-blue-600">{{ migration.progress || 0 }}%</span>
              </div>
              <div class="w-full bg-blue-100 rounded-full h-3 overflow-hidden shadow-inner">
                <div
                  class="bg-gradient-to-r from-blue-500 to-cyan-500 h-3 rounded-full transition-all duration-500 ease-out animate-pulse"
                  :style="{ width: `${migration.progress || 0}%` }"
                />
              </div>
            </div>

            <!-- Failed State -->
            <div v-if="migration.status === 'failed' && migration.error" class="mb-4 p-3 bg-gradient-to-r from-red-50 to-rose-50 rounded-lg border border-red-200">
              <div class="flex items-start">
                <svg class="w-5 h-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p class="text-sm text-red-700">{{ migration.error.substring(0, 80) }}{{ migration.error.length > 80 ? '...' : '' }}</p>
              </div>
            </div>

            <!-- Completed State -->
            <div v-if="migration.status === 'completed'" class="mb-4 p-3 bg-gradient-to-r from-emerald-50 to-green-50 rounded-lg border border-emerald-200">
              <div class="flex items-center">
                <div class="w-8 h-8 bg-gradient-to-br from-emerald-500 to-green-600 rounded-lg flex items-center justify-center mr-3 shadow-sm">
                  <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-semibold text-emerald-800">Migration Complete</p>
                  <p class="text-xs text-emerald-600">dbt project ready to download</p>
                </div>
              </div>
            </div>

            <!-- Meta Info -->
            <div class="space-y-2 text-sm text-gray-500">
              <div class="flex items-center">
                <svg class="h-4 w-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                Created {{ getTimeSince(migration.created_at) }}
              </div>

              <div v-if="migration.completed_at" class="flex items-center text-emerald-600">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                Completed {{ getTimeSince(migration.completed_at) }}
              </div>
            </div>

            <!-- Actions -->
            <div class="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
              <button
                @click.stop="viewMigration(migration)"
                class="inline-flex items-center text-sm text-cyan-600 hover:text-cyan-800 font-semibold transition-colors"
              >
                View Details
                <svg class="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </button>
              <button
                v-if="migration.status !== 'running'"
                @click.stop="deleteMigration(migration.id)"
                class="inline-flex items-center text-sm text-red-500 hover:text-red-700 font-medium transition-colors"
              >
                <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Migration card hover effect */
.migration-card {
  position: relative;
}

.migration-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 0.75rem;
  padding: 1px;
  background: linear-gradient(135deg, transparent 0%, rgba(6, 182, 212, 0.15) 100%);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.migration-card:hover::before {
  opacity: 1;
}
</style>
