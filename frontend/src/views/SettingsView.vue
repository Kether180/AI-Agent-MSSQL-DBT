<script setup lang="ts">
import { ref } from 'vue'

// Database Connections
const connections = ref([
  {
    id: 1,
    name: 'Production MSSQL',
    type: 'mssql',
    host: 'prod-db.example.com',
    database: 'ecommerce_db',
    status: 'connected'
  },
  {
    id: 2,
    name: 'Staging MSSQL',
    type: 'mssql',
    host: 'staging-db.example.com',
    database: 'ecommerce_staging',
    status: 'disconnected'
  }
])

// Notification Settings
const notifications = ref({
  migrationComplete: true,
  migrationFailed: true,
  dailyReport: false,
  weeklyReport: true
})

// API Keys
const apiKeys = ref([
  { id: 1, name: 'Production API Key', prefix: 'dm_prod_', created: '2024-01-15', lastUsed: '2 hours ago' },
  { id: 2, name: 'Development API Key', prefix: 'dm_dev_', created: '2024-02-20', lastUsed: 'Never' }
])

const showAddConnectionModal = ref(false)
const showAddApiKeyModal = ref(false)
const isSaving = ref(false)

// New connection form
const newConnection = ref({
  name: '',
  type: 'mssql',
  host: '',
  port: '1433',
  database: '',
  username: '',
  password: ''
})

const testConnection = async (connection: any) => {
  // Simulate connection test
  connection.status = 'testing'
  await new Promise(resolve => setTimeout(resolve, 2000))
  connection.status = Math.random() > 0.3 ? 'connected' : 'error'
}

const deleteConnection = (id: number) => {
  if (confirm('Are you sure you want to delete this connection?')) {
    connections.value = connections.value.filter(c => c.id !== id)
  }
}

const deleteApiKey = (id: number) => {
  if (confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
    apiKeys.value = apiKeys.value.filter(k => k.id !== id)
  }
}

const saveNotifications = async () => {
  isSaving.value = true
  await new Promise(resolve => setTimeout(resolve, 1000))
  isSaving.value = false
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'connected': return 'bg-green-100 text-green-800'
    case 'disconnected': return 'bg-gray-100 text-gray-800'
    case 'testing': return 'bg-blue-100 text-blue-800'
    case 'error': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
  }
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
                    <p class="text-sm text-gray-500">{{ connection.host }} / {{ connection.database }}</p>
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

          <div v-if="connections.length === 0" class="px-6 py-12 text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No connections</h3>
            <p class="mt-1 text-sm text-gray-500">Get started by adding a database connection.</p>
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
                    <span class="font-mono">{{ key.prefix }}••••••••</span>
                    <span>Created {{ key.created }}</span>
                    <span>Last used: {{ key.lastUsed }}</span>
                  </div>
                </div>
                <button
                  @click="deleteApiKey(key.id)"
                  class="text-sm text-red-600 hover:text-red-900"
                >
                  Revoke
                </button>
              </div>
            </li>
          </ul>
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
  </div>
</template>
