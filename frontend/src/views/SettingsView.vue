<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/services/api'
import type { DatabaseConnection, APIKey, CreateConnectionRequest } from '@/types'

const { t } = useI18n()

// Loading states
const isLoading = ref(false)
const connectionsLoading = ref(false)
const apiKeysLoading = ref(false)
const isSaving = ref(false)

// Error states
const errorMessage = ref('')
const successMessage = ref('')

// Database Connections
const connections = ref<(DatabaseConnection & { status?: string })[]>([])

// Notification Settings
const notifications = ref({
  migrationComplete: true,
  migrationFailed: true,
  dailyReport: false,
  weeklyReport: true
})

// API Keys
const apiKeys = ref<APIKey[]>([])
const newApiKeyResult = ref<{ key: string; name: string } | null>(null)

const showAddConnectionModal = ref(false)
const showAddApiKeyModal = ref(false)

// New connection form
const newConnection = ref<CreateConnectionRequest>({
  name: '',
  db_type: 'mssql',
  host: '',
  port: 1433,
  database_name: '',
  username: '',
  password: '',
  use_windows_auth: false,
  is_source: true
})

// New API key form
const newApiKeyName = ref('')
const newApiKeyRateLimit = ref(1000)

// Fetch connections on mount
onMounted(async () => {
  await Promise.all([
    fetchConnections(),
    fetchApiKeys()
  ])
})

const fetchConnections = async () => {
  connectionsLoading.value = true
  try {
    const data = await api.getConnections()
    connections.value = data.map((c: DatabaseConnection) => ({
      ...c,
      status: 'disconnected'
    }))
  } catch (err: any) {
    console.error('Failed to fetch connections:', err)
  } finally {
    connectionsLoading.value = false
  }
}

const fetchApiKeys = async () => {
  apiKeysLoading.value = true
  try {
    apiKeys.value = await api.getApiKeys()
  } catch (err: any) {
    console.error('Failed to fetch API keys:', err)
  } finally {
    apiKeysLoading.value = false
  }
}

const testConnection = async (connection: DatabaseConnection & { status?: string }) => {
  connection.status = 'testing'
  try {
    const result = await api.testConnection(connection.id)
    connection.status = result.success ? 'connected' : 'error'
    if (!result.success) {
      showError(result.message || 'Connection test failed')
    } else {
      showSuccess('Connection successful!')
    }
  } catch (err: any) {
    connection.status = 'error'
    showError(err.message || 'Failed to test connection')
  }
}

const deleteConnection = async (id: number) => {
  if (confirm('Are you sure you want to delete this connection?')) {
    try {
      await api.deleteConnection(id)
      connections.value = connections.value.filter(c => c.id !== id)
      showSuccess('Connection deleted')
    } catch (err: any) {
      showError(err.message || 'Failed to delete connection')
    }
  }
}

const addConnection = async () => {
  if (!newConnection.value.name || !newConnection.value.host || !newConnection.value.database_name) {
    showError('Please fill in all required fields')
    return
  }

  isLoading.value = true
  try {
    const created = await api.createConnection(newConnection.value)
    connections.value.unshift({ ...created, status: 'disconnected' })
    showAddConnectionModal.value = false
    resetNewConnectionForm()
    showSuccess('Connection created successfully')
  } catch (err: any) {
    showError(err.message || 'Failed to create connection')
  } finally {
    isLoading.value = false
  }
}

const resetNewConnectionForm = () => {
  newConnection.value = {
    name: '',
    db_type: 'mssql',
    host: '',
    port: 1433,
    database_name: '',
    username: '',
    password: '',
    use_windows_auth: false,
    is_source: true
  }
}

const createApiKey = async () => {
  if (!newApiKeyName.value) {
    showError('Please enter a name for the API key')
    return
  }

  isLoading.value = true
  try {
    const result = await api.createApiKey({
      name: newApiKeyName.value,
      rate_limit: newApiKeyRateLimit.value
    })
    // Show the key to the user (only shown once)
    newApiKeyResult.value = { key: result.key, name: result.name }
    await fetchApiKeys()
    newApiKeyName.value = ''
    newApiKeyRateLimit.value = 1000
  } catch (err: any) {
    showError(err.message || 'Failed to create API key')
  } finally {
    isLoading.value = false
  }
}

const closeApiKeyResult = () => {
  newApiKeyResult.value = null
  showAddApiKeyModal.value = false
}

const deleteApiKey = async (id: number) => {
  if (confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
    try {
      await api.deleteApiKey(id)
      apiKeys.value = apiKeys.value.filter(k => k.id !== id)
      showSuccess('API key revoked')
    } catch (err: any) {
      showError(err.message || 'Failed to revoke API key')
    }
  }
}

const toggleApiKey = async (key: APIKey) => {
  try {
    const result = await api.toggleApiKey(key.id)
    key.is_active = result.is_active
    showSuccess(result.is_active ? 'API key activated' : 'API key deactivated')
  } catch (err: any) {
    showError(err.message || 'Failed to toggle API key')
  }
}

const saveNotifications = async () => {
  isSaving.value = true
  // For now, just simulate save (notifications API not implemented yet)
  await new Promise(resolve => setTimeout(resolve, 500))
  isSaving.value = false
  showSuccess('Notification preferences saved')
}

const getStatusColor = (status: string | undefined) => {
  switch (status) {
    case 'connected': return 'bg-gradient-to-r from-emerald-100 to-green-100 text-emerald-800 border border-emerald-200'
    case 'disconnected': return 'bg-gradient-to-r from-gray-100 to-slate-100 text-gray-800 border border-gray-200'
    case 'testing': return 'bg-gradient-to-r from-blue-100 to-cyan-100 text-blue-800 border border-blue-200'
    case 'error': return 'bg-gradient-to-r from-red-100 to-rose-100 text-red-800 border border-red-200'
    default: return 'bg-gradient-to-r from-gray-100 to-slate-100 text-gray-800 border border-gray-200'
  }
}

const showError = (message: string) => {
  errorMessage.value = message
  successMessage.value = ''
  setTimeout(() => { errorMessage.value = '' }, 5000)
}

const showSuccess = (message: string) => {
  successMessage.value = message
  errorMessage.value = ''
  setTimeout(() => { successMessage.value = '' }, 3000)
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text)
  showSuccess('Copied to clipboard!')
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/30">
    <!-- Header with gradient -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-8">
          <div class="flex items-center">
            <div class="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-xl p-3 mr-4 shadow-lg shadow-cyan-500/25">
              <svg class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
            </div>
            <div>
              <h1 class="text-3xl font-bold text-white">{{ t('settings.title') }}</h1>
              <p class="mt-1 text-slate-300">
                {{ t('settings.subtitle') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <div class="max-w-4xl mx-auto space-y-8">
        <!-- Database Connections -->
        <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
          <div class="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-slate-50 to-white">
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <div class="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-lg p-2 mr-3 shadow-lg shadow-cyan-500/25">
                  <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                  </svg>
                </div>
                <div>
                  <h2 class="text-lg font-semibold text-slate-800">{{ t('settings.databaseConnections') }}</h2>
                  <p class="text-sm text-slate-500">
                    {{ t('settings.manageMssqlConnections') }}
                  </p>
                </div>
              </div>
              <button
                @click="showAddConnectionModal = true"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-lg text-sm font-medium rounded-xl text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 transition-all duration-200 hover:shadow-xl hover:scale-105"
              >
                <svg class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                {{ t('settings.addConnection') }}
              </button>
            </div>
          </div>

          <ul class="divide-y divide-gray-100">
            <li v-for="connection in connections" :key="connection.id" class="px-6 py-4 hover:bg-gradient-to-r hover:from-cyan-50/50 hover:to-transparent transition-colors">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <div class="flex-shrink-0 bg-gradient-to-br from-slate-100 to-slate-200 rounded-xl p-3">
                    <svg class="h-8 w-8 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                    </svg>
                  </div>
                  <div class="ml-4">
                    <h3 class="text-sm font-semibold text-slate-800">{{ connection.name }}</h3>
                    <p class="text-sm text-slate-500">{{ connection.host }} / {{ connection.database_name }}</p>
                  </div>
                </div>
                <div class="flex items-center space-x-4">
                  <span
                    :class="[
                      'inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold',
                      getStatusColor(connection.status)
                    ]"
                  >
                    <svg v-if="connection.status === 'testing'" class="animate-spin -ml-0.5 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    {{ connection.status === 'testing' ? t('settings.testing') : t('settings.' + connection.status) }}
                  </span>
                  <button
                    @click="testConnection(connection)"
                    class="text-sm font-medium text-cyan-600 hover:text-cyan-700 transition-colors"
                  >
                    {{ t('settings.test') }}
                  </button>
                  <button
                    @click="deleteConnection(connection.id)"
                    class="text-sm font-medium text-red-500 hover:text-red-700 transition-colors"
                  >
                    {{ t('settings.delete') }}
                  </button>
                </div>
              </div>
            </li>
          </ul>

          <div v-if="connections.length === 0 && !connectionsLoading" class="px-6 py-16 text-center">
            <div class="mx-auto h-20 w-20 rounded-full bg-gradient-to-br from-cyan-100 to-teal-100 flex items-center justify-center">
              <svg class="h-10 w-10 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
              </svg>
            </div>
            <h3 class="mt-4 text-lg font-semibold text-slate-800">{{ t('settings.noConnections') }}</h3>
            <p class="mt-2 text-sm text-slate-500">{{ t('settings.getStartedConnection') }}</p>
          </div>

          <div v-if="connectionsLoading" class="px-6 py-12 text-center">
            <div class="relative">
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="h-12 w-12 rounded-full border-4 border-cyan-100"></div>
              </div>
              <svg class="animate-spin h-12 w-12 mx-auto text-cyan-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
            </div>
            <p class="mt-4 text-sm text-slate-500 font-medium">{{ t('settings.loadingConnections') }}</p>
          </div>
        </div>

        <!-- API Keys -->
        <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
          <div class="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-slate-50 to-white">
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg p-2 mr-3 shadow-lg shadow-indigo-500/25">
                  <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
                  </svg>
                </div>
                <div>
                  <h2 class="text-lg font-semibold text-slate-800">{{ t('settings.apiKeys') }}</h2>
                  <p class="text-sm text-slate-500">
                    {{ t('settings.manageApiKeys') }}
                  </p>
                </div>
              </div>
              <button
                @click="showAddApiKeyModal = true"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-lg text-sm font-medium rounded-xl text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 hover:shadow-xl hover:scale-105"
              >
                <svg class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                {{ t('settings.generateApiKey') }}
              </button>
            </div>
          </div>

          <ul class="divide-y divide-gray-100">
            <li v-for="key in apiKeys" :key="key.id" class="px-6 py-4 hover:bg-gradient-to-r hover:from-indigo-50/50 hover:to-transparent transition-colors">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-sm font-semibold text-slate-800">{{ key.name }}</h3>
                  <div class="mt-1 flex items-center space-x-4 text-sm text-slate-500">
                    <span class="font-mono bg-slate-100 px-2 py-0.5 rounded">{{ key.key ? key.key.substring(0, 8) : 'dm_' }}••••••••</span>
                    <span>{{ t('settings.created') }} {{ formatDate(key.created_at) }}</span>
                    <span>{{ t('settings.lastUsed') }}: {{ key.last_used_at ? formatDate(key.last_used_at) : t('settings.never') }}</span>
                    <span :class="[
                      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold',
                      key.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                    ]">
                      {{ key.is_active ? t('settings.active') : t('settings.inactive') }}
                    </span>
                  </div>
                </div>
                <div class="flex items-center space-x-3">
                  <button
                    @click="toggleApiKey(key)"
                    class="text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
                  >
                    {{ key.is_active ? t('settings.deactivate') : t('settings.activate') }}
                  </button>
                  <button
                    @click="deleteApiKey(key.id)"
                    class="text-sm font-medium text-red-500 hover:text-red-700 transition-colors"
                  >
                    {{ t('settings.revoke') }}
                  </button>
                </div>
              </div>
            </li>
          </ul>

          <div v-if="apiKeys.length === 0 && !apiKeysLoading" class="px-6 py-16 text-center">
            <div class="mx-auto h-20 w-20 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
              <svg class="h-10 w-10 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
              </svg>
            </div>
            <h3 class="mt-4 text-lg font-semibold text-slate-800">{{ t('settings.noApiKeys') }}</h3>
            <p class="mt-2 text-sm text-slate-500">{{ t('settings.generateApiKeyAccess') }}</p>
          </div>

          <div v-if="apiKeysLoading" class="px-6 py-12 text-center">
            <div class="relative">
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="h-12 w-12 rounded-full border-4 border-indigo-100"></div>
              </div>
              <svg class="animate-spin h-12 w-12 mx-auto text-indigo-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
            </div>
            <p class="mt-4 text-sm text-slate-500 font-medium">{{ t('settings.loadingApiKeys') }}</p>
          </div>
        </div>

        <!-- Notifications -->
        <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
          <div class="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-slate-50 to-white">
            <div class="flex items-center">
              <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg p-2 mr-3 shadow-lg shadow-amber-500/25">
                <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
                </svg>
              </div>
              <div>
                <h2 class="text-lg font-semibold text-slate-800">{{ t('settings.notifications') }}</h2>
                <p class="text-sm text-slate-500">
                  {{ t('settings.configureNotifications') }}
                </p>
              </div>
            </div>
          </div>

          <div class="px-6 py-5 space-y-6">
            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl border border-emerald-100">
              <div>
                <h3 class="text-sm font-semibold text-slate-800">{{ t('settings.migrationComplete') }}</h3>
                <p class="text-sm text-slate-500">{{ t('settings.migrationCompleteDesc') }}</p>
              </div>
              <button
                @click="notifications.migrationComplete = !notifications.migrationComplete"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2',
                  notifications.migrationComplete ? 'bg-gradient-to-r from-emerald-500 to-green-500' : 'bg-gray-200'
                ]"
              >
                <span
                  :class="[
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    notifications.migrationComplete ? 'translate-x-5' : 'translate-x-0'
                  ]"
                />
              </button>
            </div>

            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-red-50 to-rose-50 rounded-xl border border-red-100">
              <div>
                <h3 class="text-sm font-semibold text-slate-800">{{ t('settings.migrationFailed') }}</h3>
                <p class="text-sm text-slate-500">{{ t('settings.migrationFailedDesc') }}</p>
              </div>
              <button
                @click="notifications.migrationFailed = !notifications.migrationFailed"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2',
                  notifications.migrationFailed ? 'bg-gradient-to-r from-red-500 to-rose-500' : 'bg-gray-200'
                ]"
              >
                <span
                  :class="[
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    notifications.migrationFailed ? 'translate-x-5' : 'translate-x-0'
                  ]"
                />
              </button>
            </div>

            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-100">
              <div>
                <h3 class="text-sm font-semibold text-slate-800">{{ t('settings.dailyReport') }}</h3>
                <p class="text-sm text-slate-500">{{ t('settings.dailyReportDesc') }}</p>
              </div>
              <button
                @click="notifications.dailyReport = !notifications.dailyReport"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                  notifications.dailyReport ? 'bg-gradient-to-r from-blue-500 to-cyan-500' : 'bg-gray-200'
                ]"
              >
                <span
                  :class="[
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    notifications.dailyReport ? 'translate-x-5' : 'translate-x-0'
                  ]"
                />
              </button>
            </div>

            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-100">
              <div>
                <h3 class="text-sm font-semibold text-slate-800">{{ t('settings.weeklyReport') }}</h3>
                <p class="text-sm text-slate-500">{{ t('settings.weeklyReportDesc') }}</p>
              </div>
              <button
                @click="notifications.weeklyReport = !notifications.weeklyReport"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2',
                  notifications.weeklyReport ? 'bg-gradient-to-r from-indigo-500 to-purple-500' : 'bg-gray-200'
                ]"
              >
                <span
                  :class="[
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    notifications.weeklyReport ? 'translate-x-5' : 'translate-x-0'
                  ]"
                />
              </button>
            </div>
          </div>

          <div class="px-6 py-4 bg-gradient-to-r from-slate-50 to-white border-t border-gray-100">
            <button
              @click="saveNotifications"
              :disabled="isSaving"
              class="inline-flex items-center px-5 py-2.5 border border-transparent shadow-lg text-sm font-medium rounded-xl text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 disabled:opacity-50 transition-all duration-200 hover:shadow-xl hover:scale-105"
            >
              <svg v-if="isSaving" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              {{ isSaving ? t('settings.saving') : t('settings.saveChanges') }}
            </button>
          </div>
        </div>

        <!-- Danger Zone -->
        <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border-2 border-red-200 overflow-hidden">
          <div class="px-6 py-5 border-b border-red-100 bg-gradient-to-r from-red-50 to-rose-50">
            <div class="flex items-center">
              <div class="bg-gradient-to-br from-red-500 to-rose-600 rounded-lg p-2 mr-3 shadow-lg shadow-red-500/25">
                <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
              </div>
              <div>
                <h2 class="text-lg font-semibold text-red-600">{{ t('settings.dangerZone') }}</h2>
                <p class="text-sm text-slate-500">
                  {{ t('settings.dangerZoneDesc') }}
                </p>
              </div>
            </div>
          </div>

          <div class="px-6 py-5 space-y-4">
            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-red-50/50 to-transparent rounded-xl">
              <div>
                <h3 class="text-sm font-semibold text-slate-800">{{ t('settings.deleteAllMigrations') }}</h3>
                <p class="text-sm text-slate-500">{{ t('settings.deleteAllMigrationsDesc') }}</p>
              </div>
              <button class="px-4 py-2 border border-red-300 text-sm font-semibold rounded-xl text-red-700 bg-white hover:bg-red-50 transition-colors shadow-sm">
                {{ t('settings.deleteAll') }}
              </button>
            </div>

            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-red-50/50 to-transparent rounded-xl">
              <div>
                <h3 class="text-sm font-semibold text-slate-800">{{ t('settings.deleteAccount') }}</h3>
                <p class="text-sm text-slate-500">{{ t('settings.deleteAccountDesc') }}</p>
              </div>
              <button class="px-4 py-2 border border-red-300 text-sm font-semibold rounded-xl text-red-700 bg-white hover:bg-red-50 transition-colors shadow-sm">
                {{ t('settings.deleteAccount') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast notifications -->
    <div v-if="errorMessage || successMessage" class="fixed bottom-4 right-4 z-50">
      <div v-if="errorMessage" class="bg-gradient-to-r from-red-100 to-rose-100 border border-red-300 text-red-800 px-5 py-3 rounded-xl shadow-lg">
        <div class="flex items-center">
          <svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          {{ errorMessage }}
        </div>
      </div>
      <div v-if="successMessage" class="bg-gradient-to-r from-emerald-100 to-green-100 border border-emerald-300 text-emerald-800 px-5 py-3 rounded-xl shadow-lg">
        <div class="flex items-center">
          <svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          {{ successMessage }}
        </div>
      </div>
    </div>

    <!-- Add Connection Modal -->
    <div v-if="showAddConnectionModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" @click="showAddConnectionModal = false"></div>
        <div class="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 border border-gray-200">
          <h3 class="text-xl font-semibold text-slate-800 mb-6">{{ t('settings.addDbConnection') }}</h3>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">{{ t('settings.connectionName') }}</label>
              <input v-model="newConnection.name" type="text" class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors" placeholder="My Database">
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">{{ t('settings.databaseType') }}</label>
              <select v-model="newConnection.db_type" class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors">
                <option value="mssql">Microsoft SQL Server</option>
                <option value="postgres">PostgreSQL</option>
                <option value="mysql">MySQL</option>
              </select>
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div class="col-span-2">
                <label class="block text-sm font-semibold text-slate-700 mb-1">{{ t('settings.host') }}</label>
                <input v-model="newConnection.host" type="text" class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors" placeholder="localhost">
              </div>
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">{{ t('settings.port') }}</label>
                <input v-model.number="newConnection.port" type="number" class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors" placeholder="1433">
              </div>
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">{{ t('settings.databaseName') }}</label>
              <input v-model="newConnection.database_name" type="text" class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors" placeholder="my_database">
            </div>

            <div class="flex items-center p-3 bg-slate-50 rounded-xl">
              <input v-model="newConnection.use_windows_auth" type="checkbox" class="h-4 w-4 text-cyan-600 focus:ring-cyan-500 border-gray-300 rounded">
              <label class="ml-3 block text-sm font-medium text-slate-700">{{ t('settings.useWindowsAuth') }}</label>
            </div>

            <div v-if="!newConnection.use_windows_auth" class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">{{ t('settings.username') }}</label>
                <input v-model="newConnection.username" type="text" class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors" placeholder="sa">
              </div>
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">{{ t('auth.password') }}</label>
                <input v-model="newConnection.password" type="password" class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors">
              </div>
            </div>
          </div>

          <div class="mt-6 flex justify-end space-x-3">
            <button @click="showAddConnectionModal = false" class="px-5 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors">
              {{ t('settings.cancel') }}
            </button>
            <button @click="addConnection" :disabled="isLoading" class="px-5 py-2.5 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 disabled:opacity-50 transition-all duration-200">
              {{ isLoading ? t('settings.adding') : t('settings.addConnection') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add API Key Modal -->
    <div v-if="showAddApiKeyModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" @click="closeApiKeyResult"></div>
        <div class="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 border border-gray-200">
          <!-- Show key result if just created -->
          <template v-if="newApiKeyResult">
            <h3 class="text-xl font-semibold text-slate-800 mb-4">{{ t('settings.apiKeyCreated') }}</h3>
            <div class="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl p-4 mb-4">
              <p class="text-sm text-amber-800 mb-3">
                {{ t('settings.copyKeyNow') }}
              </p>
              <div class="flex items-center space-x-2">
                <code class="flex-1 bg-white px-4 py-3 rounded-lg text-sm font-mono break-all border border-amber-200">{{ newApiKeyResult.key }}</code>
                <button @click="copyToClipboard(newApiKeyResult.key)" class="px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl text-sm font-semibold hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 shadow-lg">
                  {{ t('settings.copy') }}
                </button>
              </div>
            </div>
            <button @click="closeApiKeyResult" class="w-full px-5 py-3 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 transition-all duration-200">
              {{ t('settings.done') }}
            </button>
          </template>

          <!-- Show form if not yet created -->
          <template v-else>
            <h3 class="text-xl font-semibold text-slate-800 mb-6">{{ t('settings.generateApiKey') }}</h3>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">{{ t('settings.keyName') }}</label>
                <input v-model="newApiKeyName" type="text" class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors" placeholder="Production API Key">
              </div>

              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">{{ t('settings.rateLimit') }}</label>
                <input v-model.number="newApiKeyRateLimit" type="number" class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors" min="100" max="10000">
              </div>
            </div>

            <div class="mt-6 flex justify-end space-x-3">
              <button @click="showAddApiKeyModal = false" class="px-5 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors">
                {{ t('settings.cancel') }}
              </button>
              <button @click="createApiKey" :disabled="isLoading" class="px-5 py-2.5 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 transition-all duration-200">
                {{ isLoading ? t('settings.generating') : t('settings.generateKey') }}
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
