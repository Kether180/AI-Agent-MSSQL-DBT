<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import type { DatabaseConnection, APIKey, CreateConnectionRequest } from '@/types'

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
    case 'connected': return 'bg-green-100 text-green-800'
    case 'disconnected': return 'bg-gray-100 text-gray-800'
    case 'testing': return 'bg-blue-100 text-blue-800'
    case 'error': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
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
  <div class="min-h-screen bg-gray-100">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <h1 class="text-3xl font-bold text-gray-900">Settings</h1>
          <p class="mt-1 text-sm text-gray-500">
            Manage your account settings and preferences
          </p>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <div class="max-w-4xl mx-auto space-y-8">
        <!-- Database Connections -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-5 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-lg font-medium text-gray-900">Database Connections</h2>
                <p class="mt-1 text-sm text-gray-500">
                  Manage your MSSQL database connections
                </p>
              </div>
              <button
                @click="showAddConnectionModal = true"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
              >
                <svg class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                Add Connection
              </button>
            </div>
          </div>

          <ul class="divide-y divide-gray-200">
            <li v-for="connection in connections" :key="connection.id" class="px-6 py-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <div class="flex-shrink-0">
                    <svg class="h-10 w-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                    </svg>
                  </div>
                  <div class="ml-4">
                    <h3 class="text-sm font-medium text-gray-900">{{ connection.name }}</h3>
                    <p class="text-sm text-gray-500">{{ connection.host }} / {{ connection.database_name }}</p>
                  </div>
                </div>
                <div class="flex items-center space-x-4">
                  <span
                    :class="[
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      getStatusColor(connection.status)
                    ]"
                  >
                    <svg v-if="connection.status === 'testing'" class="animate-spin -ml-0.5 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    {{ connection.status === 'testing' ? 'Testing...' : connection.status }}
                  </span>
                  <button
                    @click="testConnection(connection)"
                    class="text-sm text-indigo-600 hover:text-indigo-900"
                  >
                    Test
                  </button>
                  <button
                    @click="deleteConnection(connection.id)"
                    class="text-sm text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </li>
          </ul>

          <div v-if="connections.length === 0 && !connectionsLoading" class="px-6 py-12 text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No connections</h3>
            <p class="mt-1 text-sm text-gray-500">Get started by adding a database connection.</p>
          </div>

          <div v-if="connectionsLoading" class="px-6 py-8 text-center">
            <svg class="animate-spin mx-auto h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <p class="mt-2 text-sm text-gray-500">Loading connections...</p>
          </div>
        </div>

        <!-- API Keys -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-5 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-lg font-medium text-gray-900">API Keys</h2>
                <p class="mt-1 text-sm text-gray-500">
                  Manage API keys for programmatic access
                </p>
              </div>
              <button
                @click="showAddApiKeyModal = true"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
              >
                <svg class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                Generate API Key
              </button>
            </div>
          </div>

          <ul class="divide-y divide-gray-200">
            <li v-for="key in apiKeys" :key="key.id" class="px-6 py-4">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-sm font-medium text-gray-900">{{ key.name }}</h3>
                  <div class="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                    <span class="font-mono">{{ key.key ? key.key.substring(0, 8) : 'dm_' }}••••••••</span>
                    <span>Created {{ formatDate(key.created_at) }}</span>
                    <span>Last used: {{ key.last_used_at ? formatDate(key.last_used_at) : 'Never' }}</span>
                    <span :class="key.is_active ? 'text-green-600' : 'text-red-600'">
                      {{ key.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </div>
                </div>
                <div class="flex items-center space-x-3">
                  <button
                    @click="toggleApiKey(key)"
                    class="text-sm text-indigo-600 hover:text-indigo-900"
                  >
                    {{ key.is_active ? 'Deactivate' : 'Activate' }}
                  </button>
                  <button
                    @click="deleteApiKey(key.id)"
                    class="text-sm text-red-600 hover:text-red-900"
                  >
                    Revoke
                  </button>
                </div>
              </div>
            </li>
          </ul>

          <div v-if="apiKeys.length === 0 && !apiKeysLoading" class="px-6 py-12 text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No API keys</h3>
            <p class="mt-1 text-sm text-gray-500">Generate an API key for programmatic access.</p>
          </div>

          <div v-if="apiKeysLoading" class="px-6 py-8 text-center">
            <svg class="animate-spin mx-auto h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <p class="mt-2 text-sm text-gray-500">Loading API keys...</p>
          </div>
        </div>

        <!-- Notifications -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-5 border-b border-gray-200">
            <h2 class="text-lg font-medium text-gray-900">Notifications</h2>
            <p class="mt-1 text-sm text-gray-500">
              Configure how you want to be notified
            </p>
          </div>

          <div class="px-6 py-5 space-y-6">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900">Migration Complete</h3>
                <p class="text-sm text-gray-500">Get notified when a migration completes successfully</p>
              </div>
              <button
                @click="notifications.migrationComplete = !notifications.migrationComplete"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2',
                  notifications.migrationComplete ? 'bg-indigo-600' : 'bg-gray-200'
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

            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900">Migration Failed</h3>
                <p class="text-sm text-gray-500">Get notified when a migration fails</p>
              </div>
              <button
                @click="notifications.migrationFailed = !notifications.migrationFailed"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2',
                  notifications.migrationFailed ? 'bg-indigo-600' : 'bg-gray-200'
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

            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900">Daily Report</h3>
                <p class="text-sm text-gray-500">Receive a daily summary of migrations</p>
              </div>
              <button
                @click="notifications.dailyReport = !notifications.dailyReport"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2',
                  notifications.dailyReport ? 'bg-indigo-600' : 'bg-gray-200'
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

            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900">Weekly Report</h3>
                <p class="text-sm text-gray-500">Receive a weekly summary of migrations</p>
              </div>
              <button
                @click="notifications.weeklyReport = !notifications.weeklyReport"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2',
                  notifications.weeklyReport ? 'bg-indigo-600' : 'bg-gray-200'
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

          <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-lg">
            <button
              @click="saveNotifications"
              :disabled="isSaving"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
            >
              <svg v-if="isSaving" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              {{ isSaving ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </div>

        <!-- Danger Zone -->
        <div class="bg-white shadow rounded-lg border-2 border-red-200">
          <div class="px-6 py-5 border-b border-gray-200">
            <h2 class="text-lg font-medium text-red-600">Danger Zone</h2>
            <p class="mt-1 text-sm text-gray-500">
              Irreversible and destructive actions
            </p>
          </div>

          <div class="px-6 py-5 space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900">Delete All Migrations</h3>
                <p class="text-sm text-gray-500">Permanently delete all migration history and data</p>
              </div>
              <button class="px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50">
                Delete All
              </button>
            </div>

            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900">Delete Account</h3>
                <p class="text-sm text-gray-500">Permanently delete your account and all data</p>
              </div>
              <button class="px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50">
                Delete Account
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast notifications -->
    <div v-if="errorMessage || successMessage" class="fixed bottom-4 right-4 z-50">
      <div v-if="errorMessage" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg shadow-lg">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg shadow-lg">
        {{ successMessage }}
      </div>
    </div>

    <!-- Add Connection Modal -->
    <div v-if="showAddConnectionModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showAddConnectionModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Add Database Connection</h3>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Connection Name</label>
              <input v-model="newConnection.name" type="text" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2" placeholder="My Database">
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Database Type</label>
              <select v-model="newConnection.db_type" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2">
                <option value="mssql">Microsoft SQL Server</option>
                <option value="postgres">PostgreSQL</option>
                <option value="mysql">MySQL</option>
              </select>
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div class="col-span-2">
                <label class="block text-sm font-medium text-gray-700">Host</label>
                <input v-model="newConnection.host" type="text" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2" placeholder="localhost">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Port</label>
                <input v-model.number="newConnection.port" type="number" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2" placeholder="1433">
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Database Name</label>
              <input v-model="newConnection.database_name" type="text" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2" placeholder="my_database">
            </div>

            <div class="flex items-center">
              <input v-model="newConnection.use_windows_auth" type="checkbox" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded">
              <label class="ml-2 block text-sm text-gray-900">Use Windows Authentication</label>
            </div>

            <div v-if="!newConnection.use_windows_auth" class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Username</label>
                <input v-model="newConnection.username" type="text" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2" placeholder="sa">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Password</label>
                <input v-model="newConnection.password" type="password" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2">
              </div>
            </div>
          </div>

          <div class="mt-6 flex justify-end space-x-3">
            <button @click="showAddConnectionModal = false" class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
              Cancel
            </button>
            <button @click="addConnection" :disabled="isLoading" class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50">
              {{ isLoading ? 'Adding...' : 'Add Connection' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add API Key Modal -->
    <div v-if="showAddApiKeyModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="closeApiKeyResult"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
          <!-- Show key result if just created -->
          <template v-if="newApiKeyResult">
            <h3 class="text-lg font-medium text-gray-900 mb-4">API Key Created</h3>
            <div class="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
              <p class="text-sm text-yellow-800 mb-2">
                Copy this key now. You won't be able to see it again!
              </p>
              <div class="flex items-center space-x-2">
                <code class="flex-1 bg-gray-100 px-3 py-2 rounded text-sm font-mono break-all">{{ newApiKeyResult.key }}</code>
                <button @click="copyToClipboard(newApiKeyResult.key)" class="px-3 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700">
                  Copy
                </button>
              </div>
            </div>
            <button @click="closeApiKeyResult" class="w-full px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700">
              Done
            </button>
          </template>

          <!-- Show form if not yet created -->
          <template v-else>
            <h3 class="text-lg font-medium text-gray-900 mb-4">Generate API Key</h3>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Key Name</label>
                <input v-model="newApiKeyName" type="text" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2" placeholder="Production API Key">
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Rate Limit (requests/hour)</label>
                <input v-model.number="newApiKeyRateLimit" type="number" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border px-3 py-2" min="100" max="10000">
              </div>
            </div>

            <div class="mt-6 flex justify-end space-x-3">
              <button @click="showAddApiKeyModal = false" class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
                Cancel
              </button>
              <button @click="createApiKey" :disabled="isLoading" class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50">
                {{ isLoading ? 'Generating...' : 'Generate Key' }}
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
