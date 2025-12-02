<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMigrationsStore } from '@/stores/migrations'

const route = useRoute()
const router = useRouter()
const store = useMigrationsStore()

const migrationId = computed(() => Number(route.params.id))
const migration = computed(() => store.currentMigration)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

// Polling for status updates
let pollInterval: ReturnType<typeof setInterval> | null = null

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800'
}

const statusIcons: Record<string, string> = {
  pending: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  running: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
  completed: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  failed: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
}

function formatDate(date?: string): string {
  if (!date) return '-'
  return new Date(date).toLocaleString()
}

function formatDuration(start: string, end?: string): string {
  const startDate = new Date(start)
  const endDate = end ? new Date(end) : new Date()
  const diff = Math.floor((endDate.getTime() - startDate.getTime()) / 1000)

  if (diff < 60) return `${diff}s`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`
  return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`
}

async function handleStart() {
  if (!migration.value) return
  try {
    await store.startMigration(migration.value.id)
    await store.fetchMigration(migrationId.value)
  } catch (err) {
    console.error('Failed to start migration:', err)
  }
}

async function handleStop() {
  if (!migration.value) return
  try {
    await store.stopMigration(migration.value.id)
    await store.fetchMigration(migrationId.value)
  } catch (err) {
    console.error('Failed to stop migration:', err)
  }
}

async function handleRetry() {
  if (!migration.value) return
  try {
    await store.retryMigration(migration.value.id)
    await store.fetchMigration(migrationId.value)
  } catch (err) {
    console.error('Failed to retry migration:', err)
  }
}

async function handleDelete() {
  if (!migration.value) return
  if (!confirm('Are you sure you want to delete this migration?')) return

  try {
    await store.deleteMigration(migration.value.id)
    router.push('/migrations')
  } catch (err) {
    console.error('Failed to delete migration:', err)
  }
}

function goBack() {
  router.push('/migrations')
}

onMounted(async () => {
  await store.fetchMigration(migrationId.value)

  // Poll for updates if migration is running
  pollInterval = setInterval(async () => {
    if (migration.value?.status === 'running') {
      await store.fetchMigration(migrationId.value)
    }
  }, 3000)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <button
        @click="goBack"
        class="flex items-center text-gray-600 hover:text-gray-900 mb-4"
      >
        <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Migrations
      </button>

      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900">Migration Details</h1>
        <div class="flex gap-2">
          <button
            v-if="migration?.status === 'pending'"
            @click="handleStart"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Start Migration
          </button>
          <button
            v-if="migration?.status === 'running'"
            @click="handleStop"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
            </svg>
            Stop Migration
          </button>
          <button
            v-if="migration?.status === 'failed'"
            @click="handleRetry"
            class="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Retry Migration
          </button>
          <button
            v-if="migration?.status !== 'running'"
            @click="handleDelete"
            class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !migration" class="flex justify-center py-12">
      <svg class="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex items-center">
        <svg class="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="text-red-800">{{ error }}</span>
      </div>
    </div>

    <!-- Migration Details -->
    <div v-else-if="migration" class="space-y-6">
      <!-- Status Card -->
      <div class="bg-white rounded-lg shadow-sm border p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">{{ migration.name }}</h2>
          <span
            :class="['px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1', statusColors[migration.status]]"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statusIcons[migration.status]" />
            </svg>
            {{ migration.status.charAt(0).toUpperCase() + migration.status.slice(1) }}
          </span>
        </div>

        <!-- Progress Bar -->
        <div v-if="migration.status === 'running' || migration.progress > 0" class="mb-4">
          <div class="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{{ migration.progress }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-3">
            <div
              class="h-3 rounded-full transition-all duration-500"
              :class="migration.status === 'completed' ? 'bg-green-500' : migration.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'"
              :style="{ width: `${migration.progress}%` }"
            ></div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="migration.error" class="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <div class="flex items-start">
            <svg class="w-5 h-5 text-red-600 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p class="text-sm font-medium text-red-800">Error</p>
              <p class="text-sm text-red-700">{{ migration.error }}</p>
            </div>
          </div>
        </div>

        <!-- Details Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p class="text-sm text-gray-500">Source Database</p>
            <p class="font-medium text-gray-900">{{ migration.source_database }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Target Project</p>
            <p class="font-medium text-gray-900">{{ migration.target_project }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Tables</p>
            <p class="font-medium text-gray-900">{{ migration.tables_count }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Duration</p>
            <p class="font-medium text-gray-900">{{ formatDuration(migration.created_at, migration.completed_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Timeline Card -->
      <div class="bg-white rounded-lg shadow-sm border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Timeline</h3>
        <div class="space-y-4">
          <div class="flex items-start">
            <div class="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-900">Migration Created</p>
              <p class="text-sm text-gray-500">{{ formatDate(migration.created_at) }}</p>
            </div>
          </div>

          <div v-if="migration.status !== 'pending'" class="flex items-start">
            <div class="flex-shrink-0 w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
              <svg class="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-900">Migration Started</p>
              <p class="text-sm text-gray-500">{{ formatDate(migration.created_at) }}</p>
            </div>
          </div>

          <div v-if="migration.status === 'completed'" class="flex items-start">
            <div class="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-900">Migration Completed</p>
              <p class="text-sm text-gray-500">{{ formatDate(migration.completed_at) }}</p>
            </div>
          </div>

          <div v-if="migration.status === 'failed'" class="flex items-start">
            <div class="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
              <svg class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-900">Migration Failed</p>
              <p class="text-sm text-gray-500">{{ migration.error || 'Unknown error' }}</p>
            </div>
          </div>

          <div v-if="migration.status === 'running'" class="flex items-start">
            <div class="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <svg class="w-4 h-4 text-blue-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-900">In Progress</p>
              <p class="text-sm text-gray-500">Processing {{ migration.progress }}% complete...</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Info Card -->
      <div class="bg-white rounded-lg shadow-sm border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Migration Information</h3>
        <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt class="text-sm text-gray-500">Migration ID</dt>
            <dd class="font-mono text-sm text-gray-900">{{ migration.id }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500">User ID</dt>
            <dd class="font-mono text-sm text-gray-900">{{ migration.user_id }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500">Created At</dt>
            <dd class="text-sm text-gray-900">{{ formatDate(migration.created_at) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500">Completed At</dt>
            <dd class="text-sm text-gray-900">{{ formatDate(migration.completed_at) }}</dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>
