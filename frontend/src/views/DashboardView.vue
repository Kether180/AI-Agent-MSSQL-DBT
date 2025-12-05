<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useMigrationsStore } from '@/stores/migrations'
import { api } from '@/services/api'
import type { DashboardStats } from '@/types'

const { t, locale } = useI18n()
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
const currentTime = ref(new Date())
let timeInterval: number | null = null
let refreshInterval: number | null = null

// Command palette
const showCommandPalette = ref(false)
const commandSearch = ref('')

// Computed
const userName = computed(() => {
  if (authStore.user?.first_name) return authStore.user.first_name
  return authStore.user?.email?.split('@')[0] || 'User'
})

const greeting = computed(() => {
  const hour = currentTime.value.getHours()
  if (hour < 12) return t('dashboard.goodMorning')
  if (hour < 18) return t('dashboard.goodAfternoon')
  return t('dashboard.goodEvening')
})

const formattedTime = computed(() => {
  return currentTime.value.toLocaleTimeString(localeMap[locale.value] || 'en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
})

const formattedDate = computed(() => {
  return currentTime.value.toLocaleDateString(localeMap[locale.value] || 'en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric'
  })
})

const successRateColor = computed(() => {
  const rate = stats.value.success_rate
  if (rate >= 90) return 'text-emerald-600'
  if (rate >= 70) return 'text-amber-600'
  return 'text-red-600'
})

const successRateGradient = computed(() => {
  const rate = stats.value.success_rate
  if (rate >= 90) return 'from-emerald-500 to-green-500'
  if (rate >= 70) return 'from-amber-500 to-yellow-500'
  return 'from-red-500 to-rose-500'
})

const systemHealth = computed(() => {
  const completed = stats.value.completed_migrations
  const total = stats.value.total_migrations
  const running = stats.value.running_migrations

  if (running > 0) return { status: 'active', label: t('dashboard.systemActive'), color: 'emerald' }
  if (total === 0) return { status: 'idle', label: t('dashboard.systemIdle'), color: 'slate' }
  if (stats.value.success_rate >= 90) return { status: 'healthy', label: t('dashboard.systemHealthy'), color: 'emerald' }
  if (stats.value.success_rate >= 70) return { status: 'warning', label: t('dashboard.systemWarning'), color: 'amber' }
  return { status: 'critical', label: t('dashboard.systemCritical'), color: 'red' }
})

// Sparkline data (simulated for visual effect)
const sparklineData = computed(() => {
  return [30, 45, 28, 50, 65, 40, 55, 70, 45, 60, 75, stats.value.success_rate]
})

// Methods
const fetchDashboardData = async () => {
  isLoading.value = true
  try {
    const [statsResponse] = await Promise.all([
      api.getDashboardStats().catch(() => null),
      migrationsStore.fetchMigrations()
    ])

    if (statsResponse) {
      stats.value = statsResponse
    } else {
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

const getStatusBadge = (status: string): { class: string; text: string; dotColor: string } => {
  const badges: Record<string, { class: string; textKey: string; dotColor: string }> = {
    completed: { class: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20', textKey: 'dashboard.status.completed', dotColor: 'bg-emerald-500' },
    running: { class: 'bg-blue-50 text-blue-700 ring-blue-600/20', textKey: 'dashboard.status.running', dotColor: 'bg-blue-500' },
    failed: { class: 'bg-red-50 text-red-700 ring-red-600/20', textKey: 'dashboard.status.failed', dotColor: 'bg-red-500' },
    pending: { class: 'bg-amber-50 text-amber-700 ring-amber-600/20', textKey: 'dashboard.status.pending', dotColor: 'bg-amber-500' }
  }
  const badge = badges[status] ?? badges.pending!
  return { class: badge.class, text: t(badge.textKey), dotColor: badge.dotColor }
}

const localeMap: Record<string, string> = {
  'en': 'en-US',
  'da': 'da-DK',
  'de': 'de-DE',
  'es': 'es-ES',
  'pt': 'pt-PT',
  'no': 'nb-NO',
  'sv': 'sv-SE'
}

const formatDate = (dateString: string) => {
  const browserLocale = localeMap[locale.value] || 'en-US'
  return new Date(dateString).toLocaleDateString(browserLocale, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getRelativeTime = (dateString: string) => {
  const now = new Date()
  const date = new Date(dateString)
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return t('dashboard.justNow')
  if (minutes < 60) return `${minutes}m ${t('dashboard.ago')}`
  if (hours < 24) return `${hours}h ${t('dashboard.ago')}`
  return `${days}d ${t('dashboard.ago')}`
}

const goToMigration = (id: number) => {
  router.push(`/migrations/${id}`)
}

const handleKeydown = (e: KeyboardEvent) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    showCommandPalette.value = !showCommandPalette.value
  }
  if (e.key === 'Escape') {
    showCommandPalette.value = false
  }
}

const navigateTo = (path: string) => {
  router.push(path)
  showCommandPalette.value = false
  commandSearch.value = ''
}

// Lifecycle
onMounted(() => {
  fetchDashboardData()

  // Update time every second
  timeInterval = window.setInterval(() => {
    currentTime.value = new Date()
  }, 1000)

  // Refresh data every 30 seconds
  refreshInterval = window.setInterval(fetchDashboardData, 30000)

  // Command palette keyboard shortcut
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
  if (refreshInterval) clearInterval(refreshInterval)
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/30">
    <!-- Premium Header with Time -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-2xl relative overflow-hidden">
      <!-- Animated background pattern -->
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500 rounded-full filter blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500 rounded-full filter blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>

      <div class="px-4 sm:px-6 lg:px-8 relative">
        <div class="py-8">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div class="animate-fade-in">
              <div class="flex items-center space-x-3 mb-2">
                <span class="text-slate-400 text-sm font-medium">{{ formattedDate }}</span>
                <span class="text-slate-600">•</span>
                <span class="text-cyan-400 text-sm font-mono font-medium">{{ formattedTime }}</span>
              </div>
              <h1 class="text-3xl lg:text-4xl font-bold text-white">
                {{ greeting }}, <span class="bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">{{ userName }}</span>
              </h1>
              <p class="mt-2 text-slate-300 text-lg">
                {{ $t('dashboard.subtitle') }}
              </p>
            </div>

            <!-- System Health + Quick Actions -->
            <div class="mt-6 lg:mt-0 flex items-center space-x-4">
              <!-- System Health Indicator -->
              <div class="bg-white/10 backdrop-blur-sm rounded-2xl px-5 py-3 border border-white/10">
                <div class="flex items-center space-x-3">
                  <div class="relative">
                    <div :class="[
                      'w-3 h-3 rounded-full',
                      systemHealth.color === 'emerald' ? 'bg-emerald-500' : '',
                      systemHealth.color === 'amber' ? 'bg-amber-500' : '',
                      systemHealth.color === 'red' ? 'bg-red-500' : '',
                      systemHealth.color === 'slate' ? 'bg-slate-500' : ''
                    ]"></div>
                    <div :class="[
                      'absolute inset-0 w-3 h-3 rounded-full animate-ping opacity-75',
                      systemHealth.color === 'emerald' ? 'bg-emerald-500' : '',
                      systemHealth.color === 'amber' ? 'bg-amber-500' : '',
                      systemHealth.color === 'red' ? 'bg-red-500' : '',
                      systemHealth.color === 'slate' ? 'bg-slate-500' : ''
                    ]" v-if="systemHealth.status === 'active'"></div>
                  </div>
                  <div>
                    <p class="text-xs text-slate-400 uppercase tracking-wide font-medium">{{ $t('dashboard.systemStatus') }}</p>
                    <p class="text-white font-semibold">{{ systemHealth.label }}</p>
                  </div>
                </div>
              </div>

              <!-- Command Palette Trigger -->
              <button
                @click="showCommandPalette = true"
                class="hidden lg:flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-xl px-4 py-2.5 border border-white/10 hover:bg-white/20 transition-all group"
              >
                <svg class="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <span class="text-slate-400 text-sm group-hover:text-white transition-colors">{{ $t('dashboard.quickSearch') }}</span>
                <kbd class="ml-2 px-2 py-0.5 text-xs font-mono bg-white/10 rounded text-slate-400">⌘K</kbd>
              </button>

              <!-- New Migration CTA -->
              <router-link
                to="/migrations/new"
                class="inline-flex items-center px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 shadow-lg shadow-cyan-500/25 hover:shadow-xl hover:shadow-cyan-500/30 transition-all duration-200 hover:scale-105"
              >
                <svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                {{ $t('dashboard.newMigration') }}
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <!-- Bento Grid Stats -->
      <div class="grid grid-cols-12 gap-5">
        <!-- Large Success Rate Card with Chart -->
        <div class="col-span-12 lg:col-span-4 bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden">
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center space-x-3">
                <div class="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-xl p-2.5 shadow-lg shadow-cyan-500/25">
                  <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                  </svg>
                </div>
                <span class="text-sm font-semibold text-slate-500">{{ $t('dashboard.successRate') }}</span>
              </div>
              <span class="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-1 rounded-full">{{ $t('dashboard.last30Days') }}</span>
            </div>

            <div class="flex items-end justify-between">
              <div>
                <div :class="['text-5xl font-bold', successRateColor]">
                  {{ isLoading ? '...' : stats.success_rate }}%
                </div>
                <p class="mt-1 text-sm text-slate-500">
                  <span class="text-emerald-600 font-medium">+2.5%</span> {{ $t('dashboard.fromLastMonth') }}
                </p>
              </div>

              <!-- Mini Sparkline Chart -->
              <div class="flex items-end h-16 space-x-1">
                <div v-for="(value, index) in sparklineData" :key="index"
                  :class="['w-2 rounded-t-sm transition-all duration-300', `bg-gradient-to-t ${successRateGradient}`]"
                  :style="{ height: `${value}%`, opacity: 0.4 + (index / sparklineData.length) * 0.6 }">
                </div>
              </div>
            </div>

            <!-- Progress Ring -->
            <div class="mt-6">
              <div class="relative h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  :class="['h-full rounded-full transition-all duration-1000 ease-out bg-gradient-to-r', successRateGradient]"
                  :style="{ width: `${stats.success_rate}%` }">
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats Cards Grid -->
        <div class="col-span-12 lg:col-span-8 grid grid-cols-2 lg:grid-cols-4 gap-5">
          <!-- Total Migrations -->
          <div class="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 p-5">
            <div class="flex items-center justify-between mb-3">
              <div class="bg-gradient-to-br from-slate-600 to-slate-700 rounded-xl p-2 shadow-lg shadow-slate-500/25">
                <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                </svg>
              </div>
            </div>
            <p class="text-sm font-semibold text-slate-500">{{ $t('dashboard.totalMigrations') }}</p>
            <p class="text-3xl font-bold text-slate-800 mt-1">{{ isLoading ? '...' : stats.total_migrations }}</p>
          </div>

          <!-- Completed -->
          <div class="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 p-5">
            <div class="flex items-center justify-between mb-3">
              <div class="bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl p-2 shadow-lg shadow-emerald-500/25">
                <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
            </div>
            <p class="text-sm font-semibold text-slate-500">{{ $t('dashboard.completed') }}</p>
            <p class="text-3xl font-bold text-emerald-600 mt-1">{{ isLoading ? '...' : stats.completed_migrations }}</p>
          </div>

          <!-- Running -->
          <div class="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 p-5 relative overflow-hidden">
            <div v-if="stats.running_migrations > 0" class="absolute top-3 right-3">
              <span class="flex h-3 w-3">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
              </span>
            </div>
            <div class="flex items-center justify-between mb-3">
              <div class="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl p-2 shadow-lg shadow-blue-500/25">
                <svg :class="['h-5 w-5 text-white', stats.running_migrations > 0 ? 'animate-spin' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
              </div>
            </div>
            <p class="text-sm font-semibold text-slate-500">{{ $t('dashboard.running') }}</p>
            <p class="text-3xl font-bold text-blue-600 mt-1">{{ isLoading ? '...' : stats.running_migrations }}</p>
          </div>

          <!-- Failed -->
          <div class="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 p-5">
            <div class="flex items-center justify-between mb-3">
              <div class="bg-gradient-to-br from-red-500 to-rose-600 rounded-xl p-2 shadow-lg shadow-red-500/25">
                <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
            </div>
            <p class="text-sm font-semibold text-slate-500">{{ $t('dashboard.failed') }}</p>
            <p class="text-3xl font-bold text-red-600 mt-1">{{ isLoading ? '...' : stats.failed_migrations }}</p>
          </div>
        </div>
      </div>

      <!-- Two Column Layout -->
      <div class="mt-8 grid grid-cols-12 gap-6">
        <!-- Recent Migrations - Larger -->
        <div class="col-span-12 lg:col-span-8">
          <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
            <div class="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-slate-50 to-white">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <div class="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-xl p-2.5 mr-3 shadow-lg shadow-cyan-500/25">
                    <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  </div>
                  <div>
                    <h3 class="text-lg font-semibold text-slate-800">{{ $t('dashboard.recentMigrations') }}</h3>
                    <p class="text-sm text-slate-500">{{ $t('dashboard.latestActivity') }}</p>
                  </div>
                </div>
                <router-link
                  to="/migrations"
                  class="inline-flex items-center px-4 py-2 text-sm font-medium text-cyan-600 hover:text-cyan-700 hover:bg-cyan-50 rounded-xl transition-all"
                >
                  {{ $t('dashboard.viewAll') }}
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
                  <div class="h-16 w-16 rounded-full border-4 border-cyan-100"></div>
                </div>
                <svg class="animate-spin h-16 w-16 mx-auto text-cyan-600" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
              </div>
              <p class="mt-4 text-sm text-slate-500 font-medium">{{ $t('dashboard.loading') }}</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="recentMigrations.length === 0" class="px-6 py-16 text-center">
              <div class="mx-auto h-24 w-24 rounded-full bg-gradient-to-br from-cyan-100 to-teal-100 flex items-center justify-center">
                <svg class="h-12 w-12 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
                </svg>
              </div>
              <h3 class="mt-4 text-lg font-semibold text-slate-800">{{ $t('dashboard.noMigrations') }}</h3>
              <p class="mt-2 text-sm text-slate-500 max-w-sm mx-auto">{{ $t('dashboard.getStarted') }}</p>
              <div class="mt-6">
                <router-link
                  to="/migrations/new"
                  class="inline-flex items-center px-6 py-3 border border-transparent shadow-lg text-sm font-semibold rounded-xl text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 transition-all duration-200 hover:shadow-xl hover:scale-105"
                >
                  <svg class="mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                  </svg>
                  {{ $t('dashboard.createFirstMigration') }}
                </router-link>
              </div>
            </div>

            <!-- Migrations List -->
            <ul v-else role="list" class="divide-y divide-gray-100">
              <li
                v-for="migration in recentMigrations"
                :key="migration.id"
                @click="goToMigration(migration.id)"
                class="px-6 py-4 hover:bg-gradient-to-r hover:from-cyan-50/50 hover:to-transparent cursor-pointer transition-all duration-200 group"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center flex-1 min-w-0">
                    <div :class="[
                      'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mr-4',
                      migration.status === 'completed' ? 'bg-emerald-100' : '',
                      migration.status === 'running' ? 'bg-blue-100' : '',
                      migration.status === 'failed' ? 'bg-red-100' : '',
                      migration.status === 'pending' ? 'bg-amber-100' : ''
                    ]">
                      <svg v-if="migration.status === 'completed'" class="h-5 w-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                      <svg v-else-if="migration.status === 'running'" class="h-5 w-5 text-blue-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                      </svg>
                      <svg v-else-if="migration.status === 'failed'" class="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                      <svg v-else class="h-5 w-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h4 class="text-sm font-semibold text-slate-800 group-hover:text-cyan-600 truncate transition-colors">
                        {{ migration.name }}
                      </h4>
                      <p class="mt-0.5 text-xs text-slate-500">
                        {{ getRelativeTime(migration.created_at) }}
                      </p>
                    </div>
                  </div>
                  <div class="ml-4 flex-shrink-0 flex items-center space-x-3">
                    <span
                      :class="[
                        'inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ring-1 ring-inset',
                        getStatusBadge(migration.status).class
                      ]"
                    >
                      <span :class="['w-1.5 h-1.5 rounded-full mr-1.5', getStatusBadge(migration.status).dotColor]"></span>
                      {{ getStatusBadge(migration.status).text }}
                    </span>
                    <svg class="h-5 w-5 text-slate-400 group-hover:text-cyan-500 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                  </div>
                </div>

                <!-- Progress Bar -->
                <div v-if="migration.status === 'running' && migration.progress" class="mt-3 ml-14">
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-xs font-medium text-blue-600">{{ $t('dashboard.inProgress') }}</span>
                    <span class="text-xs font-bold text-blue-600">{{ migration.progress }}%</span>
                  </div>
                  <div class="w-full bg-blue-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      class="bg-gradient-to-r from-blue-500 to-cyan-500 h-1.5 rounded-full transition-all duration-500 ease-out"
                      :style="{ width: `${migration.progress}%` }"
                    />
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <!-- Right Sidebar - Quick Actions & AI Agents -->
        <div class="col-span-12 lg:col-span-4 space-y-6">
          <!-- Quick Actions -->
          <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
            <div class="px-5 py-4 border-b border-gray-100 bg-gradient-to-r from-slate-50 to-white">
              <div class="flex items-center">
                <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg p-2 mr-3 shadow-lg shadow-indigo-500/25">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                </div>
                <h3 class="text-sm font-semibold text-slate-800">{{ $t('dashboard.quickActions') }}</h3>
              </div>
            </div>
            <div class="p-4 space-y-2">
              <router-link to="/migrations/new" class="flex items-center p-3 rounded-xl hover:bg-indigo-50 transition-colors group">
                <div class="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg p-2 mr-3 group-hover:shadow-lg group-hover:shadow-indigo-200 transition-shadow">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-800 group-hover:text-indigo-600 transition-colors">{{ $t('dashboard.newMigration') }}</p>
                  <p class="text-xs text-slate-500">{{ $t('dashboard.startNewMigration') }}</p>
                </div>
              </router-link>

              <router-link to="/migrations" class="flex items-center p-3 rounded-xl hover:bg-emerald-50 transition-colors group">
                <div class="bg-gradient-to-br from-emerald-500 to-green-600 rounded-lg p-2 mr-3 group-hover:shadow-lg group-hover:shadow-emerald-200 transition-shadow">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-800 group-hover:text-emerald-600 transition-colors">{{ $t('dashboard.viewAll') }}</p>
                  <p class="text-xs text-slate-500">{{ $t('dashboard.viewAllMigrations') }}</p>
                </div>
              </router-link>

              <router-link to="/docs" class="flex items-center p-3 rounded-xl hover:bg-purple-50 transition-colors group">
                <div class="bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg p-2 mr-3 group-hover:shadow-lg group-hover:shadow-purple-200 transition-shadow">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-800 group-hover:text-purple-600 transition-colors">{{ $t('dashboard.documentation') }}</p>
                  <p class="text-xs text-slate-500">{{ $t('dashboard.learnHow') }}</p>
                </div>
              </router-link>

              <router-link to="/settings" class="flex items-center p-3 rounded-xl hover:bg-slate-100 transition-colors group">
                <div class="bg-gradient-to-br from-slate-600 to-slate-700 rounded-lg p-2 mr-3 group-hover:shadow-lg group-hover:shadow-slate-300 transition-shadow">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-800 group-hover:text-slate-700 transition-colors">{{ $t('dashboard.settings') }}</p>
                  <p class="text-xs text-slate-500">{{ $t('dashboard.manageConnections') }}</p>
                </div>
              </router-link>
            </div>
          </div>

          <!-- AI Agents Compact -->
          <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
            <div class="px-5 py-4 border-b border-gray-100 bg-gradient-to-r from-slate-50 to-white">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <div class="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-lg p-2 mr-3 shadow-lg shadow-cyan-500/25">
                    <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                    </svg>
                  </div>
                  <h3 class="text-sm font-semibold text-slate-800">{{ $t('dashboard.aiAgents') }}</h3>
                </div>
                <span class="px-2 py-0.5 text-xs font-semibold bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-full">11</span>
              </div>
            </div>
            <div class="p-4 grid grid-cols-2 gap-3">
              <router-link to="/agents/dataprep" class="p-3 rounded-xl bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-100 hover:shadow-md transition-all group">
                <div class="bg-gradient-to-br from-orange-500 to-amber-600 rounded-lg p-2 w-fit shadow-sm">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
                  </svg>
                </div>
                <p class="mt-2 text-xs font-semibold text-slate-800 group-hover:text-orange-600 transition-colors">{{ $t('dashboard.dataPrepAI') }}</p>
              </router-link>

              <router-link to="/agents/ml-finetuning" class="p-3 rounded-xl bg-gradient-to-br from-indigo-50 to-blue-50 border border-indigo-100 hover:shadow-md transition-all group">
                <div class="bg-gradient-to-br from-indigo-500 to-blue-600 rounded-lg p-2 w-fit shadow-sm">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                  </svg>
                </div>
                <p class="mt-2 text-xs font-semibold text-slate-800 group-hover:text-indigo-600 transition-colors">{{ $t('dashboard.mlFineTuning') }}</p>
              </router-link>

              <div class="p-3 rounded-xl bg-gradient-to-br from-emerald-50 to-green-50 border border-emerald-100 hover:shadow-md transition-all cursor-pointer group">
                <div class="bg-gradient-to-br from-emerald-500 to-green-600 rounded-lg p-2 w-fit shadow-sm">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                  </svg>
                </div>
                <p class="mt-2 text-xs font-semibold text-slate-800 group-hover:text-emerald-600 transition-colors">{{ $t('dashboard.dataQuality') }}</p>
              </div>

              <div class="p-3 rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 hover:shadow-md transition-all cursor-pointer group">
                <div class="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg p-2 w-fit shadow-sm">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                  </svg>
                </div>
                <p class="mt-2 text-xs font-semibold text-slate-800 group-hover:text-blue-600 transition-colors">{{ $t('dashboard.biAnalytics') }}</p>
              </div>
            </div>
            <div class="px-4 pb-4">
              <button class="w-full text-center text-xs font-medium text-cyan-600 hover:text-cyan-700 py-2 hover:bg-cyan-50 rounded-lg transition-colors">
                {{ $t('dashboard.viewAllAgents') }} →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Command Palette Modal -->
    <Teleport to="body">
      <div v-if="showCommandPalette" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex items-start justify-center min-h-screen pt-24 px-4">
          <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" @click="showCommandPalette = false"></div>
          <div class="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-gray-200">
            <div class="px-4 py-3 border-b border-gray-100">
              <div class="flex items-center">
                <svg class="h-5 w-5 text-slate-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <input
                  v-model="commandSearch"
                  type="text"
                  class="flex-1 border-0 focus:ring-0 text-slate-800 placeholder-slate-400 text-sm"
                  :placeholder="$t('dashboard.typeCommand')"
                  autofocus
                >
                <kbd class="px-2 py-0.5 text-xs font-mono bg-slate-100 rounded text-slate-400">ESC</kbd>
              </div>
            </div>
            <div class="py-2 max-h-80 overflow-y-auto">
              <div class="px-3 py-1">
                <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide">{{ $t('dashboard.quickActions') }}</p>
              </div>
              <button @click="navigateTo('/migrations/new')" class="w-full flex items-center px-4 py-2.5 hover:bg-slate-50 transition-colors">
                <div class="bg-indigo-100 rounded-lg p-1.5 mr-3">
                  <svg class="h-4 w-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                  </svg>
                </div>
                <span class="text-sm text-slate-700">{{ $t('dashboard.newMigration') }}</span>
              </button>
              <button @click="navigateTo('/migrations')" class="w-full flex items-center px-4 py-2.5 hover:bg-slate-50 transition-colors">
                <div class="bg-emerald-100 rounded-lg p-1.5 mr-3">
                  <svg class="h-4 w-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                  </svg>
                </div>
                <span class="text-sm text-slate-700">{{ $t('dashboard.viewAllMigrations') }}</span>
              </button>
              <button @click="navigateTo('/settings')" class="w-full flex items-center px-4 py-2.5 hover:bg-slate-50 transition-colors">
                <div class="bg-slate-100 rounded-lg p-1.5 mr-3">
                  <svg class="h-4 w-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                </div>
                <span class="text-sm text-slate-700">{{ $t('dashboard.settings') }}</span>
              </button>
              <button @click="navigateTo('/docs')" class="w-full flex items-center px-4 py-2.5 hover:bg-slate-50 transition-colors">
                <div class="bg-purple-100 rounded-lg p-1.5 mr-3">
                  <svg class="h-4 w-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                  </svg>
                </div>
                <span class="text-sm text-slate-700">{{ $t('dashboard.documentation') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
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
</style>
