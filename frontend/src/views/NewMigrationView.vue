<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Multi-step wizard state
const currentStep = ref(1)
const totalSteps = 4

// Form data
const formData = ref({
  // Step 1: Basic Info
  name: '',
  description: '',

  // Step 2: Source Database
  sourceType: 'mssql',
  sourceHost: '',
  sourcePort: '1433',
  sourceDatabase: '',
  sourceUsername: '',
  sourcePassword: '',

  // Step 3: Target Configuration
  targetType: 'dbt',
  targetProject: '',
  targetSchema: 'public',
  generateTests: true,
  generateDocs: true,

  // Step 4: Tables Selection
  selectedTables: [] as string[],
  includeViews: false,
  includeStoredProcedures: false
})

// Mock available tables (would come from API after connecting to source)
const availableTables = ref([
  { name: 'users', rows: 15420, selected: false },
  { name: 'orders', rows: 89432, selected: false },
  { name: 'products', rows: 2341, selected: false },
  { name: 'customers', rows: 45231, selected: false },
  { name: 'inventory', rows: 12893, selected: false },
  { name: 'transactions', rows: 234521, selected: false },
  { name: 'audit_logs', rows: 892341, selected: false },
  { name: 'settings', rows: 156, selected: false }
])

const isLoading = ref(false)
const isConnecting = ref(false)
const connectionStatus = ref<'idle' | 'success' | 'error'>('idle')

// Computed
const isStepValid = computed(() => {
  switch (currentStep.value) {
    case 1:
      return formData.value.name.length >= 3
    case 2:
      return formData.value.sourceHost &&
             formData.value.sourceDatabase &&
             formData.value.sourceUsername
    case 3:
      return formData.value.targetProject.length >= 2
    case 4:
      return formData.value.selectedTables.length > 0
    default:
      return false
  }
})

const selectedTableCount = computed(() => {
  return availableTables.value.filter(t => t.selected).length
})

// Methods
const nextStep = () => {
  if (currentStep.value < totalSteps && isStepValid.value) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const goToStep = (step: number) => {
  if (step <= currentStep.value) {
    currentStep.value = step
  }
}

const testConnection = async () => {
  isConnecting.value = true
  connectionStatus.value = 'idle'

  // Simulate connection test
  await new Promise(resolve => setTimeout(resolve, 2000))

  // Mock success (in real app, call API)
  connectionStatus.value = Math.random() > 0.3 ? 'success' : 'error'
  isConnecting.value = false
}

const toggleTable = (table: any) => {
  table.selected = !table.selected
  formData.value.selectedTables = availableTables.value
    .filter(t => t.selected)
    .map(t => t.name)
}

const selectAllTables = () => {
  availableTables.value.forEach(t => t.selected = true)
  formData.value.selectedTables = availableTables.value.map(t => t.name)
}

const deselectAllTables = () => {
  availableTables.value.forEach(t => t.selected = false)
  formData.value.selectedTables = []
}

const formatNumber = (num: number) => {
  return num.toLocaleString()
}

const handleSubmit = async () => {
  if (!isStepValid.value) return

  isLoading.value = true

  try {
    // API call would go here
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Redirect to migrations list
    router.push('/migrations')
  } catch (error) {
    console.error('Failed to create migration:', error)
    alert('Failed to create migration. Please try again.')
  } finally {
    isLoading.value = false
  }
}

const cancel = () => {
  if (confirm('Are you sure you want to cancel? All progress will be lost.')) {
    router.push('/migrations')
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <div class="flex items-center">
            <button
              @click="cancel"
              class="mr-4 text-gray-400 hover:text-gray-600"
            >
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
              </svg>
            </button>
            <div>
              <h1 class="text-3xl font-bold text-gray-900">Create New Migration</h1>
              <p class="mt-1 text-sm text-gray-500">
                Follow the steps below to configure your MSSQL to dbt migration
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <div class="max-w-4xl mx-auto">
        <!-- Progress Steps -->
        <nav aria-label="Progress" class="mb-8">
          <ol class="flex items-center">
            <li v-for="step in totalSteps" :key="step" class="relative flex-1">
              <div class="flex items-center">
                <button
                  @click="goToStep(step)"
                  :class="[
                    'relative flex h-10 w-10 items-center justify-center rounded-full',
                    step < currentStep ? 'bg-indigo-600 hover:bg-indigo-800' :
                    step === currentStep ? 'border-2 border-indigo-600 bg-white' :
                    'border-2 border-gray-300 bg-white'
                  ]"
                  :disabled="step > currentStep"
                >
                  <svg
                    v-if="step < currentStep"
                    class="h-5 w-5 text-white"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                  </svg>
                  <span
                    v-else
                    :class="[
                      step === currentStep ? 'text-indigo-600' : 'text-gray-500'
                    ]"
                  >
                    {{ step }}
                  </span>
                </button>
                <div
                  v-if="step < totalSteps"
                  :class="[
                    'ml-4 flex-1 h-0.5',
                    step < currentStep ? 'bg-indigo-600' : 'bg-gray-300'
                  ]"
                />
              </div>
              <span
                :class="[
                  'absolute -bottom-6 left-0 text-xs font-medium whitespace-nowrap',
                  step <= currentStep ? 'text-indigo-600' : 'text-gray-500'
                ]"
              >
                {{ step === 1 ? 'Basic Info' :
                   step === 2 ? 'Source DB' :
                   step === 3 ? 'Target Config' :
                   'Select Tables' }}
              </span>
            </li>
          </ol>
        </nav>

        <!-- Form Card -->
        <div class="bg-white shadow rounded-lg mt-12">
          <!-- Step 1: Basic Info -->
          <div v-if="currentStep === 1" class="p-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Basic Information</h2>

            <div class="space-y-6">
              <div>
                <label for="name" class="block text-sm font-medium text-gray-700">
                  Migration Name *
                </label>
                <input
                  id="name"
                  v-model="formData.name"
                  type="text"
                  placeholder="e.g., ecommerce-migration-v1"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
                <p class="mt-1 text-sm text-gray-500">
                  A unique name to identify this migration
                </p>
              </div>

              <div>
                <label for="description" class="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  v-model="formData.description"
                  rows="4"
                  placeholder="Describe the purpose of this migration..."
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
            </div>
          </div>

          <!-- Step 2: Source Database -->
          <div v-if="currentStep === 2" class="p-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Source Database Connection</h2>

            <div class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label for="sourceHost" class="block text-sm font-medium text-gray-700">
                    Host / Server *
                  </label>
                  <input
                    id="sourceHost"
                    v-model="formData.sourceHost"
                    type="text"
                    placeholder="localhost or IP address"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label for="sourcePort" class="block text-sm font-medium text-gray-700">
                    Port
                  </label>
                  <input
                    id="sourcePort"
                    v-model="formData.sourcePort"
                    type="text"
                    placeholder="1433"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label for="sourceDatabase" class="block text-sm font-medium text-gray-700">
                  Database Name *
                </label>
                <input
                  id="sourceDatabase"
                  v-model="formData.sourceDatabase"
                  type="text"
                  placeholder="my_database"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label for="sourceUsername" class="block text-sm font-medium text-gray-700">
                    Username *
                  </label>
                  <input
                    id="sourceUsername"
                    v-model="formData.sourceUsername"
                    type="text"
                    placeholder="sa"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label for="sourcePassword" class="block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <input
                    id="sourcePassword"
                    v-model="formData.sourcePassword"
                    type="password"
                    placeholder="********"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>

              <!-- Test Connection Button -->
              <div class="flex items-center space-x-4">
                <button
                  @click="testConnection"
                  :disabled="isConnecting || !formData.sourceHost || !formData.sourceDatabase"
                  class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  <svg v-if="isConnecting" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  <svg v-else class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                  {{ isConnecting ? 'Testing...' : 'Test Connection' }}
                </button>

                <span v-if="connectionStatus === 'success'" class="inline-flex items-center text-green-600">
                  <svg class="h-5 w-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                  </svg>
                  Connection successful
                </span>

                <span v-if="connectionStatus === 'error'" class="inline-flex items-center text-red-600">
                  <svg class="h-5 w-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                  </svg>
                  Connection failed
                </span>
              </div>
            </div>
          </div>

          <!-- Step 3: Target Configuration -->
          <div v-if="currentStep === 3" class="p-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Target dbt Configuration</h2>

            <div class="space-y-6">
              <div>
                <label for="targetProject" class="block text-sm font-medium text-gray-700">
                  dbt Project Name *
                </label>
                <input
                  id="targetProject"
                  v-model="formData.targetProject"
                  type="text"
                  placeholder="my_dbt_project"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              <div>
                <label for="targetSchema" class="block text-sm font-medium text-gray-700">
                  Target Schema
                </label>
                <input
                  id="targetSchema"
                  v-model="formData.targetSchema"
                  type="text"
                  placeholder="public"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              <div class="space-y-4">
                <h3 class="text-sm font-medium text-gray-700">Generation Options</h3>

                <div class="flex items-center">
                  <input
                    id="generateTests"
                    v-model="formData.generateTests"
                    type="checkbox"
                    class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label for="generateTests" class="ml-2 block text-sm text-gray-700">
                    Generate dbt tests (recommended)
                  </label>
                </div>

                <div class="flex items-center">
                  <input
                    id="generateDocs"
                    v-model="formData.generateDocs"
                    type="checkbox"
                    class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label for="generateDocs" class="ml-2 block text-sm text-gray-700">
                    Generate documentation
                  </label>
                </div>
              </div>

              <!-- AI Features Info -->
              <div class="bg-indigo-50 rounded-lg p-4">
                <div class="flex">
                  <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                  </div>
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-indigo-800">AI-Powered Features</h3>
                    <p class="mt-1 text-sm text-indigo-700">
                      DataMigrate AI will automatically analyze your schema and generate optimized dbt models with proper relationships, data types, and transformations.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 4: Select Tables -->
          <div v-if="currentStep === 4" class="p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-semibold text-gray-900">Select Tables to Migrate</h2>
              <div class="flex items-center space-x-4">
                <button
                  @click="selectAllTables"
                  class="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  Select All
                </button>
                <button
                  @click="deselectAllTables"
                  class="text-sm text-gray-600 hover:text-gray-800"
                >
                  Deselect All
                </button>
              </div>
            </div>

            <div class="mb-4">
              <span class="text-sm text-gray-500">
                {{ selectedTableCount }} of {{ availableTables.length }} tables selected
              </span>
            </div>

            <div class="space-y-2 max-h-96 overflow-y-auto">
              <div
                v-for="table in availableTables"
                :key="table.name"
                @click="toggleTable(table)"
                :class="[
                  'flex items-center justify-between p-4 rounded-lg border-2 cursor-pointer transition-colors',
                  table.selected
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                ]"
              >
                <div class="flex items-center">
                  <input
                    type="checkbox"
                    :checked="table.selected"
                    class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    @click.stop="toggleTable(table)"
                  />
                  <div class="ml-4">
                    <h4 class="text-sm font-medium text-gray-900">{{ table.name }}</h4>
                  </div>
                </div>
                <span class="text-sm text-gray-500">
                  {{ formatNumber(table.rows) }} rows
                </span>
              </div>
            </div>

            <!-- Additional Options -->
            <div class="mt-6 space-y-4 pt-6 border-t">
              <div class="flex items-center">
                <input
                  id="includeViews"
                  v-model="formData.includeViews"
                  type="checkbox"
                  class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label for="includeViews" class="ml-2 block text-sm text-gray-700">
                  Include Views
                </label>
              </div>

              <div class="flex items-center">
                <input
                  id="includeStoredProcedures"
                  v-model="formData.includeStoredProcedures"
                  type="checkbox"
                  class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label for="includeStoredProcedures" class="ml-2 block text-sm text-gray-700">
                  Include Stored Procedures (convert to dbt macros)
                </label>
              </div>
            </div>
          </div>

          <!-- Navigation Buttons -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between rounded-b-lg">
            <button
              v-if="currentStep > 1"
              @click="prevStep"
              class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
              </svg>
              Previous
            </button>
            <div v-else></div>

            <div class="flex space-x-3">
              <button
                @click="cancel"
                class="px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>

              <button
                v-if="currentStep < totalSteps"
                @click="nextStep"
                :disabled="!isStepValid"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
                <svg class="ml-2 -mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </button>

              <button
                v-else
                @click="handleSubmit"
                :disabled="!isStepValid || isLoading"
                class="inline-flex items-center px-6 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg v-if="isLoading" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                <svg v-else class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                {{ isLoading ? 'Creating...' : 'Create Migration' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar for table list */
.max-h-96::-webkit-scrollbar {
  width: 6px;
}

.max-h-96::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.max-h-96::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.max-h-96::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
</style>
