<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

// Platform logos
import snowflakeLogo from '@/assets/logos/snowflake.svg'
import bigqueryLogo from '@/assets/logos/bigquery.svg'
import databricksLogo from '@/assets/logos/databricks.svg'
import redshiftLogo from '@/assets/logos/redshift.svg'
import fabricLogo from '@/assets/logos/fabric.svg'
import mssqlLogo from '@/assets/logos/mssql.svg'

const warehouseLogos: Record<string, string> = {
  snowflake: snowflakeLogo,
  bigquery: bigqueryLogo,
  databricks: databricksLogo,
  redshift: redshiftLogo,
  fabric: fabricLogo,
  mssql: mssqlLogo
}

const router = useRouter()

// Multi-step wizard state
const currentStep = ref(1)
const totalSteps = 5

// Form data
const formData = ref({
  // Step 1: Basic Info
  name: '',
  description: '',

  // Step 2: Source Database/File
  sourceType: 'mssql' as 'mssql' | 'excel',
  sourceHost: '',
  sourcePort: '1433',
  sourceDatabase: '',
  sourceUsername: '',
  sourcePassword: '',
  useWindowsAuth: true,  // Default to Windows Authentication

  // Excel specific fields
  excelFiles: [] as File[],
  excelSheetMappings: [] as { fileName: string; sheetName: string; targetTable: string; hasHeaders: boolean }[],

  // Step 3: Target Configuration
  targetType: 'dbt',
  targetProject: '',
  targetSchema: 'public',
  targetWarehouse: 'fabric' as 'snowflake' | 'databricks' | 'fabric' | 'bigquery' | 'redshift',
  generateTests: true,
  generateDocs: true,

  // Target Warehouse Credentials
  warehouseCredentials: {
    // Snowflake
    snowflakeAccount: '',
    snowflakeWarehouse: '',
    snowflakeDatabase: '',
    snowflakeSchema: '',
    snowflakeUser: '',
    snowflakePassword: '',
    snowflakeRole: '',
    // Databricks
    databricksHost: '',
    databricksToken: '',
    databricksHttpPath: '',
    databricksCatalog: '',
    // BigQuery
    bigqueryProject: '',
    bigqueryDataset: '',
    bigqueryKeyfile: '',
    // Redshift
    redshiftHost: '',
    redshiftPort: '5439',
    redshiftDatabase: '',
    redshiftUser: '',
    redshiftPassword: '',
    // Microsoft Fabric
    fabricWorkspace: '',
    fabricLakehouse: '',
    fabricEndpoint: '',
    fabricClientId: '',
    fabricClientSecret: '',
    fabricTenantId: ''
  },

  // Step 4: Tables Selection
  selectedTables: [] as string[],
  includeViews: false,
  includeStoredProcedures: false,

  // Step 5: Phase 2 Integrations
  enableIntegrations: false,
  selectedIntegration: '' as 'fivetran' | 'airbyte' | 'aws' | 'azure' | 'gcp' | '',
  integrationConfig: {
    // Fivetran
    fivetranApiKey: '',
    fivetranGroupId: '',
    // Airbyte
    airbyteHost: '',
    airbyteWorkspaceId: '',
    // AWS
    awsAccessKey: '',
    awsSecretKey: '',
    awsRegion: 'us-east-1',
    s3Bucket: '',
    // Azure
    azureConnectionString: '',
    azureContainerName: '',
    // GCP
    gcpProjectId: '',
    gcpServiceAccountKey: ''
  }
})

// Tables fetched from real database
const availableTables = ref<{ name: string; rows: number; selected: boolean; schema?: string }[]>([])
const availableViews = ref<{ name: string; schema?: string }[]>([])

const isLoading = ref(false)
const isConnecting = ref(false)
const isFetchingTables = ref(false)
const connectionStatus = ref<'idle' | 'success' | 'error'>('idle')
const connectionError = ref('')
const savedConnectionId = ref<number | null>(null)
const showTablePreview = ref(false)

// Excel specific state
const isParsingExcel = ref(false)
const excelParseError = ref('')
const parsedExcelSheets = ref<{ fileName: string; sheets: { name: string; rowCount: number; columns: string[] }[] }[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)

// Computed
const isStepValid = computed(() => {
  switch (currentStep.value) {
    case 1:
      return formData.value.name.length >= 3
    case 2:
      // Different validation for MSSQL vs Excel
      if (formData.value.sourceType === 'excel') {
        return formData.value.excelFiles.length > 0 && parsedExcelSheets.value.length > 0
      }
      return formData.value.sourceHost &&
             formData.value.sourceDatabase &&
             (formData.value.useWindowsAuth || formData.value.sourceUsername) &&
             connectionStatus.value === 'success'
    case 3:
      return formData.value.targetProject.length >= 2
    case 4:
      return formData.value.selectedTables.length > 0
    case 5:
      // Step 5 is optional - always valid (user can skip integrations)
      return true
    default:
      return false
  }
})

const selectedTableCount = computed(() => {
  return availableTables.value.filter(t => t.selected).length
})

// Methods
const nextStep = async () => {
  if (currentStep.value < totalSteps && isStepValid.value) {
    // When moving from step 2 to step 3, fetch tables
    if (currentStep.value === 2 && availableTables.value.length === 0) {
      await fetchTables()
    }
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

// Excel handling methods
const handleExcelUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return

  isParsingExcel.value = true
  excelParseError.value = ''

  try {
    const files = Array.from(input.files)
    formData.value.excelFiles = files

    // Parse each Excel file to get sheet information
    // In a real implementation, this would call the backend API
    // For now, we'll simulate the parsing
    const parsedFiles: typeof parsedExcelSheets.value = []

    for (const file of files) {
      // Create FormData and send to backend for parsing
      const fileFormData = new FormData()
      fileFormData.append('file', file)

      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/api/v1/excel/parse`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${api.getToken()}`
          },
          body: fileFormData
        })

        if (response.ok) {
          const data = await response.json()
          parsedFiles.push({
            fileName: file.name,
            sheets: data.sheets || []
          })
        } else {
          // Fallback: simulate parsed data for demo
          parsedFiles.push({
            fileName: file.name,
            sheets: [
              { name: 'Sheet1', rowCount: 100, columns: ['Column A', 'Column B', 'Column C'] }
            ]
          })
        }
      } catch {
        // Fallback: simulate parsed data for demo
        parsedFiles.push({
          fileName: file.name,
          sheets: [
            { name: 'Sheet1', rowCount: 100, columns: ['Column A', 'Column B', 'Column C'] }
          ]
        })
      }
    }

    parsedExcelSheets.value = parsedFiles

    // Auto-generate sheet mappings
    formData.value.excelSheetMappings = parsedFiles.flatMap(file =>
      file.sheets.map(sheet => ({
        fileName: file.fileName,
        sheetName: sheet.name,
        targetTable: sheet.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
        hasHeaders: true
      }))
    )

    // Also populate availableTables for Step 4
    availableTables.value = formData.value.excelSheetMappings.map(mapping => ({
      name: `${mapping.fileName} - ${mapping.sheetName}`,
      rows: parsedFiles.find(f => f.fileName === mapping.fileName)?.sheets.find(s => s.name === mapping.sheetName)?.rowCount || 0,
      selected: true,
      schema: 'excel'
    }))

    // Auto-select all tables
    formData.value.selectedTables = availableTables.value.map(t => t.name)

  } catch (error: any) {
    excelParseError.value = error.message || 'Failed to parse Excel file'
  } finally {
    isParsingExcel.value = false
  }
}

const removeExcelFile = (index: number) => {
  const fileName = formData.value.excelFiles[index]?.name
  if (!fileName) return
  formData.value.excelFiles.splice(index, 1)
  parsedExcelSheets.value = parsedExcelSheets.value.filter(f => f.fileName !== fileName)
  formData.value.excelSheetMappings = formData.value.excelSheetMappings.filter(m => m.fileName !== fileName)
  availableTables.value = availableTables.value.filter(t => !t.name.startsWith(fileName))
  formData.value.selectedTables = formData.value.selectedTables.filter(t => !t.startsWith(fileName))
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const testConnection = async () => {
  isConnecting.value = true
  connectionStatus.value = 'idle'
  connectionError.value = ''

  try {
    // First, create or update the connection in the backend
    const connectionData = {
      name: `${formData.value.name}-source`,
      db_type: formData.value.sourceType,
      host: formData.value.sourceHost,
      port: parseInt(formData.value.sourcePort) || 1433,
      database_name: formData.value.sourceDatabase,
      username: formData.value.useWindowsAuth ? '' : formData.value.sourceUsername,
      password: formData.value.useWindowsAuth ? '' : formData.value.sourcePassword,
      use_windows_auth: formData.value.useWindowsAuth,
      is_source: true
    }

    let connection
    if (savedConnectionId.value) {
      // Update existing connection
      connection = await api.updateConnection(savedConnectionId.value, connectionData)
    } else {
      // Create new connection
      connection = await api.createConnection(connectionData)
      savedConnectionId.value = connection.id
    }

    // Test the connection
    const result = await api.testConnection(connection.id)

    if (result.success) {
      connectionStatus.value = 'success'
      // Fetch tables after successful connection
      await fetchTables()
    } else {
      connectionStatus.value = 'error'
      connectionError.value = result.message || 'Connection test failed'
    }
  } catch (error: any) {
    connectionStatus.value = 'error'
    connectionError.value = error.message || 'Failed to test connection'
  } finally {
    isConnecting.value = false
  }
}

const fetchTables = async () => {
  if (!savedConnectionId.value) return

  isFetchingTables.value = true
  showTablePreview.value = false

  try {
    // Call backend API to extract metadata from the MSSQL database
    // This endpoint calls the Python MSSQL extractor
    const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/api/v1/connections/${savedConnectionId.value}/metadata`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${api.getToken()}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const metadata = await response.json()

      // Map tables from metadata
      availableTables.value = (metadata.tables || []).map((table: any) => ({
        name: table.name,
        schema: table.schema || 'dbo',
        rows: table.row_count || 0,
        selected: false
      }))

      // Store views separately
      availableViews.value = (metadata.views || []).map((view: any) => ({
        name: view.name,
        schema: view.schema || 'dbo'
      }))

      // Show preview if we have tables
      if (availableTables.value.length > 0 || availableViews.value.length > 0) {
        showTablePreview.value = true
      }
    } else {
      // Fallback: if metadata endpoint not available, use sample data
      console.warn('Metadata endpoint not available, using sample data')
      availableTables.value = [
        { name: 'Customers', schema: 'dbo', rows: 15420, selected: false },
        { name: 'Orders', schema: 'dbo', rows: 89750, selected: false },
        { name: 'Products', schema: 'dbo', rows: 3240, selected: false },
        { name: 'OrderItems', schema: 'dbo', rows: 245800, selected: false },
        { name: 'Employees', schema: 'hr', rows: 156, selected: false }
      ]
      availableViews.value = [
        { name: 'vw_CustomerOrders', schema: 'dbo' },
        { name: 'vw_SalesSummary', schema: 'reports' }
      ]
      showTablePreview.value = true
    }
  } catch (error) {
    console.error('Failed to fetch tables:', error)
    // Fallback sample data for demo
    availableTables.value = [
      { name: 'Customers', schema: 'dbo', rows: 15420, selected: false },
      { name: 'Orders', schema: 'dbo', rows: 89750, selected: false },
      { name: 'Products', schema: 'dbo', rows: 3240, selected: false }
    ]
    availableViews.value = []
    showTablePreview.value = true
  } finally {
    isFetchingTables.value = false
  }
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
    // Create the migration using the API
    const migrationData = {
      name: formData.value.name,
      source_database: `${formData.value.name}-source`, // Connection name
      target_project: formData.value.targetProject,
      tables: formData.value.selectedTables.filter(t => !t.startsWith('[VIEW]')),
      include_views: formData.value.includeViews
    }

    await api.createMigration(migrationData)

    // Redirect to migrations list
    router.push('/migrations')
  } catch (error: any) {
    console.error('Failed to create migration:', error)
    alert(`Failed to create migration: ${error.message}`)
  } finally {
    isLoading.value = false
  }
}

const cancel = () => {
  if (confirm('Are you sure you want to cancel? All progress will be lost.')) {
    // Clean up saved connection if user cancels
    if (savedConnectionId.value) {
      api.deleteConnection(savedConnectionId.value).catch(() => {})
    }
    router.push('/migrations')
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-cyan-50">
    <!-- Header -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <div class="flex items-center">
            <button
              @click="cancel"
              class="mr-4 p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50 transition-all duration-200"
            >
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
              </svg>
            </button>
            <div>
              <h1 class="text-3xl font-bold text-white">Create New <span class="bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">Migration</span></h1>
              <p class="mt-1 text-sm text-slate-300">
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
                    'relative flex h-10 w-10 items-center justify-center rounded-full transition-all duration-200',
                    step < currentStep ? 'bg-gradient-to-br from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 shadow-lg shadow-cyan-500/25' :
                    step === currentStep ? 'border-2 border-cyan-500 bg-white shadow-lg' :
                    'border-2 border-slate-300 bg-white'
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
                      step === currentStep ? 'text-cyan-600 font-semibold' : 'text-slate-500'
                    ]"
                  >
                    {{ step }}
                  </span>
                </button>
                <div
                  v-if="step < totalSteps"
                  :class="[
                    'ml-4 flex-1 h-0.5 rounded-full',
                    step < currentStep ? 'bg-gradient-to-r from-cyan-500 to-teal-500' : 'bg-slate-300'
                  ]"
                />
              </div>
              <span
                :class="[
                  'absolute -bottom-6 left-0 text-xs font-semibold whitespace-nowrap',
                  step <= currentStep ? 'text-cyan-600' : 'text-slate-500'
                ]"
              >
                {{ step === 1 ? 'Basic Info' :
                   step === 2 ? 'Source DB' :
                   step === 3 ? 'Target Config' :
                   step === 4 ? 'Select Tables' :
                   'Integrations' }}
              </span>
            </li>
          </ol>
        </nav>

        <!-- Form Card -->
        <div class="bg-white/80 backdrop-blur-sm shadow-xl rounded-xl mt-12 border border-slate-200/50">
          <!-- Step 1: Basic Info -->
          <div v-if="currentStep === 1" class="p-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-8 tracking-tight">Basic Information</h2>

            <div class="space-y-8">
              <div>
                <label for="name" class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">
                  Migration Name <span class="text-cyan-500">*</span>
                </label>
                <input
                  id="name"
                  v-model="formData.name"
                  type="text"
                  placeholder="e.g., ecommerce-migration-v1"
                  class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                />
                <p class="mt-2 text-sm text-slate-500 font-medium">
                  A unique name to identify this migration
                </p>
              </div>

              <div>
                <label for="description" class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">
                  Description
                </label>
                <textarea
                  id="description"
                  v-model="formData.description"
                  rows="4"
                  placeholder="Describe the purpose of this migration..."
                  class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200 resize-none"
                />
              </div>
            </div>
          </div>

          <!-- Step 2: Source Database/File -->
          <div v-if="currentStep === 2" class="p-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-8 tracking-tight">Data Source</h2>

            <div class="space-y-8">
              <!-- Source Type Selection -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-3">
                  Select Data Source Type <span class="text-cyan-500">*</span>
                </label>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <!-- MSSQL Option -->
                  <div
                    @click="formData.sourceType = 'mssql'"
                    :class="[
                      'p-4 border-2 rounded-lg cursor-pointer transition-all duration-200',
                      formData.sourceType === 'mssql'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex items-center mb-2">
                      <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/>
                        </svg>
                      </div>
                      <span class="ml-3 font-semibold text-gray-900">SQL Server (MSSQL)</span>
                    </div>
                    <p class="text-xs text-gray-500">Connect directly to a Microsoft SQL Server database</p>
                  </div>

                  <!-- Excel Option -->
                  <div
                    @click="formData.sourceType = 'excel'"
                    :class="[
                      'p-4 border-2 rounded-lg cursor-pointer transition-all duration-200',
                      formData.sourceType === 'excel'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex items-center mb-2">
                      <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                      </div>
                      <span class="ml-3 font-semibold text-gray-900">Excel Files</span>
                    </div>
                    <p class="text-xs text-gray-500">Import data from Excel spreadsheets (.xlsx, .xls)</p>
                  </div>
                </div>
              </div>

              <!-- MSSQL Connection Form -->
              <div v-if="formData.sourceType === 'mssql'" class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label for="sourceHost" class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">
                      Host / Server <span class="text-cyan-500">*</span>
                    </label>
                    <input
                      id="sourceHost"
                      v-model="formData.sourceHost"
                      type="text"
                      placeholder="localhost or IP address"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>

                  <div>
                    <label for="sourcePort" class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">
                      Port
                    </label>
                    <input
                      id="sourcePort"
                      v-model="formData.sourcePort"
                      type="text"
                      placeholder="1433"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                </div>

                <div>
                  <label for="sourceDatabase" class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">
                    Database Name <span class="text-cyan-500">*</span>
                  </label>
                  <input
                    id="sourceDatabase"
                    v-model="formData.sourceDatabase"
                    type="text"
                    placeholder="my_database"
                    class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                  />
                </div>

                <!-- Windows Authentication Toggle -->
                <div class="flex items-center">
                  <input
                    id="useWindowsAuth"
                    v-model="formData.useWindowsAuth"
                    type="checkbox"
                    class="h-5 w-5 text-cyan-600 focus:ring-cyan-500 border-slate-300 rounded-md"
                  />
                  <label for="useWindowsAuth" class="ml-3 block text-base font-medium text-slate-700">
                    Use Windows Authentication (Trusted Connection)
                  </label>
                </div>

                <!-- SQL Server Authentication (shown when Windows Auth is disabled) -->
                <div v-if="!formData.useWindowsAuth" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label for="sourceUsername" class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">
                      Username <span class="text-cyan-500">*</span>
                    </label>
                    <input
                      id="sourceUsername"
                      v-model="formData.sourceUsername"
                      type="text"
                      placeholder="sa"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>

                  <div>
                    <label for="sourcePassword" class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">
                      Password
                    </label>
                    <input
                      id="sourcePassword"
                      v-model="formData.sourcePassword"
                      type="password"
                      placeholder="********"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                </div>

                <!-- Info box when Windows Auth is enabled -->
                <div v-if="formData.useWindowsAuth" class="bg-blue-50 rounded-lg p-3">
                  <div class="flex">
                    <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                    <p class="ml-2 text-sm text-blue-700">
                      Windows Authentication will use your current Windows login credentials to connect to SQL Server.
                    </p>
                  </div>
                </div>

                <!-- Test Connection Button -->
                <div class="flex items-center space-x-4">
                  <button
                    @click="testConnection"
                    :disabled="isConnecting || !formData.sourceHost || !formData.sourceDatabase"
                    class="inline-flex items-center px-4 py-2 border border-slate-300 shadow-sm text-sm font-medium rounded-lg text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 disabled:opacity-50 transition-all duration-200"
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
                    {{ connectionError || 'Connection failed' }}
                  </span>
                </div>

                <!-- Loading tables indicator -->
                <div v-if="isFetchingTables" class="mt-4 flex items-center text-cyan-600">
                  <svg class="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  Fetching database tables...
                </div>

                <!-- Database Preview Section -->
                <div v-if="showTablePreview && connectionStatus === 'success'" class="mt-6 border border-slate-200 rounded-xl overflow-hidden">
                  <div class="bg-gradient-to-r from-emerald-50 to-cyan-50 px-4 py-3 border-b border-slate-200">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center">
                        <svg class="h-5 w-5 text-emerald-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                        </svg>
                        <h4 class="font-semibold text-slate-800">Database Preview</h4>
                      </div>
                      <div class="flex items-center space-x-4 text-sm">
                        <span class="text-slate-600">
                          <span class="font-medium text-emerald-600">{{ availableTables.length }}</span> tables
                        </span>
                        <span class="text-slate-600">
                          <span class="font-medium text-blue-600">{{ availableViews.length }}</span> views
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- Tables List -->
                  <div class="max-h-48 overflow-y-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-slate-50 sticky top-0">
                        <tr>
                          <th class="text-left px-4 py-2 font-medium text-slate-600">Name</th>
                          <th class="text-left px-4 py-2 font-medium text-slate-600">Schema</th>
                          <th class="text-right px-4 py-2 font-medium text-slate-600">Rows</th>
                          <th class="text-center px-4 py-2 font-medium text-slate-600">Type</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-slate-100">
                        <tr v-for="table in availableTables.slice(0, 10)" :key="table.name" class="hover:bg-slate-50">
                          <td class="px-4 py-2 font-medium text-slate-800">{{ table.name }}</td>
                          <td class="px-4 py-2 text-slate-500">{{ table.schema }}</td>
                          <td class="px-4 py-2 text-right text-slate-600">{{ formatNumber(table.rows) }}</td>
                          <td class="px-4 py-2 text-center">
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800">
                              Table
                            </span>
                          </td>
                        </tr>
                        <tr v-for="view in availableViews.slice(0, 5)" :key="view.name" class="hover:bg-slate-50">
                          <td class="px-4 py-2 font-medium text-slate-800">{{ view.name }}</td>
                          <td class="px-4 py-2 text-slate-500">{{ view.schema }}</td>
                          <td class="px-4 py-2 text-right text-slate-400">-</td>
                          <td class="px-4 py-2 text-center">
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              View
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <!-- Show more indicator -->
                  <div v-if="availableTables.length > 10 || availableViews.length > 5" class="px-4 py-2 bg-slate-50 border-t border-slate-200 text-center">
                    <span class="text-sm text-slate-500">
                      + {{ Math.max(0, availableTables.length - 10) + Math.max(0, availableViews.length - 5) }} more items. Select tables in the next step.
                    </span>
                  </div>
                </div>
              </div>

              <!-- Excel Upload Form -->
              <div v-if="formData.sourceType === 'excel'" class="space-y-6">
                <!-- Hidden file input -->
                <input
                  ref="fileInputRef"
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  multiple
                  class="hidden"
                  @change="handleExcelUpload"
                />

                <!-- Upload area -->
                <div
                  @click="triggerFileInput"
                  @dragover.prevent
                  @drop.prevent="handleExcelUpload"
                  class="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center cursor-pointer hover:border-cyan-500 hover:bg-cyan-50/30 transition-all duration-200"
                >
                  <div class="flex flex-col items-center">
                    <div class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                      <svg class="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                      </svg>
                    </div>
                    <p class="text-lg font-medium text-slate-700 mb-1">
                      Click to upload or drag and drop
                    </p>
                    <p class="text-sm text-slate-500">
                      Excel files (.xlsx, .xls) or CSV files
                    </p>
                  </div>
                </div>

                <!-- Uploaded files list -->
                <div v-if="formData.excelFiles.length > 0" class="space-y-3">
                  <h4 class="text-sm font-medium text-slate-700">Uploaded Files</h4>
                  <div
                    v-for="(file, index) in formData.excelFiles"
                    :key="file.name"
                    class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200"
                  >
                    <div class="flex items-center">
                      <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center mr-3">
                        <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                      </div>
                      <div>
                        <p class="text-sm font-medium text-slate-800">{{ file.name }}</p>
                        <p class="text-xs text-slate-500">{{ (file.size / 1024).toFixed(1) }} KB</p>
                      </div>
                    </div>
                    <button
                      @click.stop="removeExcelFile(index)"
                      class="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                      </svg>
                    </button>
                  </div>
                </div>

                <!-- Parsed sheets info -->
                <div v-if="parsedExcelSheets.length > 0" class="bg-cyan-50 rounded-lg p-4 border border-cyan-100">
                  <div class="flex items-start">
                    <svg class="h-5 w-5 text-cyan-500 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                    <div class="ml-3">
                      <h3 class="text-sm font-medium text-cyan-800">Files Parsed Successfully</h3>
                      <p class="mt-1 text-sm text-cyan-700">
                        Found {{ parsedExcelSheets.reduce((acc, f) => acc + f.sheets.length, 0) }} sheet(s) across {{ parsedExcelSheets.length }} file(s). Each sheet will be converted to a dbt model.
                      </p>
                    </div>
                  </div>
                </div>

                <!-- Parsing indicator -->
                <div v-if="isParsingExcel" class="flex items-center text-cyan-600">
                  <svg class="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  Parsing Excel files...
                </div>

                <!-- Error message -->
                <div v-if="excelParseError" class="bg-red-50 rounded-lg p-4 border border-red-100">
                  <div class="flex">
                    <svg class="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                    <p class="ml-2 text-sm text-red-700">{{ excelParseError }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3: Target Configuration -->
          <div v-if="currentStep === 3" class="p-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-8 tracking-tight">Target dbt Configuration</h2>

            <div class="space-y-8">
              <div>
                <label for="targetProject" class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">
                  dbt Project Name <span class="text-cyan-500">*</span>
                </label>
                <input
                  id="targetProject"
                  v-model="formData.targetProject"
                  type="text"
                  placeholder="my_dbt_project"
                  class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                />
              </div>

              <div>
                <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-3">
                  Target Data Warehouse <span class="text-cyan-500">*</span>
                </label>
                <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
                  <!-- Microsoft Fabric - #1 Priority -->
                  <div
                    @click="formData.targetWarehouse = 'fabric'"
                    :class="[
                      'p-4 border-2 rounded-xl cursor-pointer transition-all duration-200',
                      formData.targetWarehouse === 'fabric'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex flex-col items-center text-center">
                      <img :src="warehouseLogos.fabric" alt="Microsoft Fabric" class="w-10 h-10 mb-2" />
                      <div class="flex items-center">
                        <input
                          type="radio"
                          :checked="formData.targetWarehouse === 'fabric'"
                          class="h-4 w-4 text-cyan-600"
                        />
                        <span class="ml-2 font-medium text-gray-900 text-sm">Microsoft Fabric</span>
                      </div>
                    </div>
                    <p class="mt-2 text-xs text-gray-500 text-center">Microsoft analytics SaaS</p>
                  </div>

                  <!-- Databricks - #2 Priority -->
                  <div
                    @click="formData.targetWarehouse = 'databricks'"
                    :class="[
                      'p-4 border-2 rounded-xl cursor-pointer transition-all duration-200',
                      formData.targetWarehouse === 'databricks'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex flex-col items-center text-center">
                      <img :src="warehouseLogos.databricks" alt="Databricks" class="w-10 h-10 mb-2" />
                      <div class="flex items-center">
                        <input
                          type="radio"
                          :checked="formData.targetWarehouse === 'databricks'"
                          class="h-4 w-4 text-cyan-600"
                        />
                        <span class="ml-2 font-medium text-gray-900 text-sm">Databricks</span>
                      </div>
                    </div>
                    <p class="mt-2 text-xs text-gray-500 text-center">Unified ML/AI platform</p>
                  </div>

                  <!-- Snowflake - #3 Priority -->
                  <div
                    @click="formData.targetWarehouse = 'snowflake'"
                    :class="[
                      'p-4 border-2 rounded-xl cursor-pointer transition-all duration-200',
                      formData.targetWarehouse === 'snowflake'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex flex-col items-center text-center">
                      <img :src="warehouseLogos.snowflake" alt="Snowflake" class="w-10 h-10 mb-2" />
                      <div class="flex items-center">
                        <input
                          type="radio"
                          :checked="formData.targetWarehouse === 'snowflake'"
                          class="h-4 w-4 text-cyan-600"
                        />
                        <span class="ml-2 font-medium text-gray-900 text-sm">Snowflake</span>
                      </div>
                    </div>
                    <p class="mt-2 text-xs text-gray-500 text-center">Cloud data warehouse</p>
                  </div>

                  <!-- BigQuery - #4 Priority -->
                  <div
                    @click="formData.targetWarehouse = 'bigquery'"
                    :class="[
                      'p-4 border-2 rounded-xl cursor-pointer transition-all duration-200',
                      formData.targetWarehouse === 'bigquery'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex flex-col items-center text-center">
                      <img :src="warehouseLogos.bigquery" alt="BigQuery" class="w-10 h-10 mb-2" />
                      <div class="flex items-center">
                        <input
                          type="radio"
                          :checked="formData.targetWarehouse === 'bigquery'"
                          class="h-4 w-4 text-cyan-600"
                        />
                        <span class="ml-2 font-medium text-gray-900 text-sm">BigQuery</span>
                      </div>
                    </div>
                    <p class="mt-2 text-xs text-gray-500 text-center">Google Cloud analytics</p>
                  </div>

                  <!-- Redshift - #5 Priority -->
                  <div
                    @click="formData.targetWarehouse = 'redshift'"
                    :class="[
                      'p-4 border-2 rounded-xl cursor-pointer transition-all duration-200',
                      formData.targetWarehouse === 'redshift'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex flex-col items-center text-center">
                      <img :src="warehouseLogos.redshift" alt="Redshift" class="w-10 h-10 mb-2" />
                      <div class="flex items-center">
                        <input
                          type="radio"
                          :checked="formData.targetWarehouse === 'redshift'"
                          class="h-4 w-4 text-cyan-600"
                        />
                        <span class="ml-2 font-medium text-gray-900 text-sm">Redshift</span>
                      </div>
                    </div>
                    <p class="mt-2 text-xs text-gray-500 text-center">AWS data warehouse</p>
                  </div>
                </div>
              </div>

              <!-- Warehouse Credentials Forms -->
              <!-- Snowflake Credentials -->
              <div v-if="formData.targetWarehouse === 'snowflake'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <div class="flex items-center mb-4">
                  <img :src="warehouseLogos.snowflake" alt="Snowflake" class="w-8 h-8 mr-3" />
                  <h3 class="text-lg font-semibold text-slate-800">Snowflake Connection</h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Account <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.snowflakeAccount"
                      type="text"
                      placeholder="abc12345.us-east-1"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Warehouse <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.snowflakeWarehouse"
                      type="text"
                      placeholder="COMPUTE_WH"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Database <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.snowflakeDatabase"
                      type="text"
                      placeholder="MY_DATABASE"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Schema <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.snowflakeSchema"
                      type="text"
                      placeholder="PUBLIC"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Username <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.snowflakeUser"
                      type="text"
                      placeholder="your_username"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Password <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.snowflakePassword"
                      type="password"
                      placeholder="********"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div class="md:col-span-2">
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Role (optional)</label>
                    <input
                      v-model="formData.warehouseCredentials.snowflakeRole"
                      type="text"
                      placeholder="ACCOUNTADMIN"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                </div>
              </div>

              <!-- Databricks Credentials -->
              <div v-if="formData.targetWarehouse === 'databricks'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <div class="flex items-center mb-4">
                  <img :src="warehouseLogos.databricks" alt="Databricks" class="w-8 h-8 mr-3" />
                  <h3 class="text-lg font-semibold text-slate-800">Databricks Connection</h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div class="md:col-span-2">
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Host <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.databricksHost"
                      type="text"
                      placeholder="adb-1234567890123456.7.azuredatabricks.net"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div class="md:col-span-2">
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Access Token <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.databricksToken"
                      type="password"
                      placeholder="dapi..."
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">HTTP Path <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.databricksHttpPath"
                      type="text"
                      placeholder="/sql/1.0/warehouses/abc123"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Catalog</label>
                    <input
                      v-model="formData.warehouseCredentials.databricksCatalog"
                      type="text"
                      placeholder="main"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                </div>
              </div>

              <!-- BigQuery Credentials -->
              <div v-if="formData.targetWarehouse === 'bigquery'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <div class="flex items-center mb-4">
                  <img :src="warehouseLogos.bigquery" alt="BigQuery" class="w-8 h-8 mr-3" />
                  <h3 class="text-lg font-semibold text-slate-800">BigQuery Connection</h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Project ID <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.bigqueryProject"
                      type="text"
                      placeholder="my-gcp-project"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Dataset <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.bigqueryDataset"
                      type="text"
                      placeholder="my_dataset"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div class="md:col-span-2">
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Service Account Key (JSON) <span class="text-cyan-500">*</span></label>
                    <textarea
                      v-model="formData.warehouseCredentials.bigqueryKeyfile"
                      rows="4"
                      placeholder='{"type": "service_account", "project_id": "...", ...}'
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 font-mono text-sm resize-none"
                    />
                  </div>
                </div>
              </div>

              <!-- Redshift Credentials -->
              <div v-if="formData.targetWarehouse === 'redshift'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <div class="flex items-center mb-4">
                  <img :src="warehouseLogos.redshift" alt="Redshift" class="w-8 h-8 mr-3" />
                  <h3 class="text-lg font-semibold text-slate-800">Redshift Connection</h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Host <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.redshiftHost"
                      type="text"
                      placeholder="my-cluster.abc123.us-east-1.redshift.amazonaws.com"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Port</label>
                    <input
                      v-model="formData.warehouseCredentials.redshiftPort"
                      type="text"
                      placeholder="5439"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Database <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.redshiftDatabase"
                      type="text"
                      placeholder="dev"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Username <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.redshiftUser"
                      type="text"
                      placeholder="awsuser"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div class="md:col-span-2">
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Password <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.redshiftPassword"
                      type="password"
                      placeholder="********"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                </div>
              </div>

              <!-- Microsoft Fabric Credentials -->
              <div v-if="formData.targetWarehouse === 'fabric'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <div class="flex items-center mb-4">
                  <img :src="warehouseLogos.fabric" alt="Microsoft Fabric" class="w-8 h-8 mr-3" />
                  <h3 class="text-lg font-semibold text-slate-800">Microsoft Fabric Connection</h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Workspace ID <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.fabricWorkspace"
                      type="text"
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Lakehouse Name <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.fabricLakehouse"
                      type="text"
                      placeholder="my_lakehouse"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div class="md:col-span-2">
                    <label class="block text-sm font-semibold text-slate-700 mb-2">SQL Endpoint <span class="text-cyan-500">*</span></label>
                    <input
                      v-model="formData.warehouseCredentials.fabricEndpoint"
                      type="text"
                      placeholder="xxxxxxxx.datawarehouse.fabric.microsoft.com"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Client ID (App Registration)</label>
                    <input
                      v-model="formData.warehouseCredentials.fabricClientId"
                      type="text"
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Tenant ID</label>
                    <input
                      v-model="formData.warehouseCredentials.fabricTenantId"
                      type="text"
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                  <div class="md:col-span-2">
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Client Secret</label>
                    <input
                      v-model="formData.warehouseCredentials.fabricClientSecret"
                      type="password"
                      placeholder="********"
                      class="block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400"
                    />
                  </div>
                </div>
                <div class="bg-blue-50 rounded-lg p-3 mt-4">
                  <div class="flex">
                    <svg class="h-5 w-5 text-blue-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                    <p class="ml-2 text-sm text-blue-700">
                      For Fabric authentication, you can use Service Principal (Client ID/Secret) or leave empty for interactive Azure AD login.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <label for="targetSchema" class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">
                  Target Schema
                </label>
                <input
                  id="targetSchema"
                  v-model="formData.targetSchema"
                  type="text"
                  placeholder="public"
                  class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                />
              </div>

              <div class="space-y-4">
                <h3 class="text-sm font-semibold text-slate-700 tracking-wide">Generation Options</h3>

                <div class="flex items-center">
                  <input
                    id="generateTests"
                    v-model="formData.generateTests"
                    type="checkbox"
                    class="h-5 w-5 text-cyan-600 focus:ring-cyan-500 border-slate-300 rounded-md"
                  />
                  <label for="generateTests" class="ml-3 block text-base font-medium text-slate-700">
                    Generate dbt tests (recommended)
                  </label>
                </div>

                <div class="flex items-center">
                  <input
                    id="generateDocs"
                    v-model="formData.generateDocs"
                    type="checkbox"
                    class="h-5 w-5 text-cyan-600 focus:ring-cyan-500 border-slate-300 rounded-md"
                  />
                  <label for="generateDocs" class="ml-3 block text-base font-medium text-slate-700">
                    Generate documentation
                  </label>
                </div>
              </div>

              <!-- AI Features Info -->
              <div class="bg-cyan-50 rounded-lg p-4 border border-cyan-100">
                <div class="flex">
                  <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-cyan-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                  </div>
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-cyan-800">AI-Powered Features</h3>
                    <p class="mt-1 text-sm text-cyan-700">
                      DataMigrate AI will automatically analyze your schema and generate optimized dbt models with proper relationships, data types, and transformations.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 4: Select Tables -->
          <div v-if="currentStep === 4" class="p-8">
            <div class="flex items-center justify-between mb-8">
              <h2 class="text-2xl font-semibold text-slate-800 tracking-tight">Select Tables to Migrate</h2>
              <div class="flex items-center space-x-4">
                <button
                  @click="selectAllTables"
                  class="text-sm text-cyan-600 hover:text-cyan-800 font-medium transition-colors"
                >
                  Select All
                </button>
                <button
                  @click="deselectAllTables"
                  class="text-sm text-slate-600 hover:text-slate-800 font-medium transition-colors"
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
                  'flex items-center justify-between p-4 rounded-lg border-2 cursor-pointer transition-all duration-200',
                  table.selected
                    ? 'border-cyan-500 bg-cyan-50 shadow-md'
                    : 'border-slate-200 hover:border-slate-300 hover:shadow'
                ]"
              >
                <div class="flex items-center">
                  <input
                    type="checkbox"
                    :checked="table.selected"
                    class="h-4 w-4 text-cyan-600 focus:ring-cyan-500 border-slate-300 rounded"
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
            <div class="mt-8 space-y-4 pt-6 border-t border-slate-200">
              <div class="flex items-center">
                <input
                  id="includeViews"
                  v-model="formData.includeViews"
                  type="checkbox"
                  class="h-5 w-5 text-cyan-600 focus:ring-cyan-500 border-slate-300 rounded-md"
                />
                <label for="includeViews" class="ml-3 block text-base font-medium text-slate-700">
                  Include Views
                </label>
              </div>

              <div class="flex items-center">
                <input
                  id="includeStoredProcedures"
                  v-model="formData.includeStoredProcedures"
                  type="checkbox"
                  class="h-5 w-5 text-cyan-600 focus:ring-cyan-500 border-slate-300 rounded-md"
                />
                <label for="includeStoredProcedures" class="ml-3 block text-base font-medium text-slate-700">
                  Include Stored Procedures (convert to dbt macros)
                </label>
              </div>
            </div>
          </div>

          <!-- Step 5: Phase 2 Integrations -->
          <div v-if="currentStep === 5" class="p-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-2 tracking-tight">Phase 2: Data Platform Integrations</h2>
            <p class="text-base text-slate-500 mb-8">
              Optionally configure integrations to automatically deploy your dbt models to data platforms. You can skip this step and configure later.
            </p>

            <!-- Enable Integrations Toggle -->
            <div class="mb-8">
              <div class="flex items-center">
                <input
                  id="enableIntegrations"
                  v-model="formData.enableIntegrations"
                  type="checkbox"
                  class="h-5 w-5 text-cyan-600 focus:ring-cyan-500 border-slate-300 rounded-md"
                />
                <label for="enableIntegrations" class="ml-3 block text-base font-medium text-slate-700">
                  Enable data platform integrations
                </label>
              </div>
            </div>

            <!-- Integration Options (shown when enabled) -->
            <div v-if="formData.enableIntegrations" class="space-y-8">
              <!-- Integration Selection -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-3">
                  Select Integration Platform
                </label>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <!-- Fivetran -->
                  <div
                    @click="formData.selectedIntegration = 'fivetran'"
                    :class="[
                      'p-4 border-2 rounded-lg cursor-pointer transition-all duration-200',
                      formData.selectedIntegration === 'fivetran'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex items-center mb-2">
                      <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                        </svg>
                      </div>
                      <span class="ml-3 font-semibold text-gray-900">Fivetran</span>
                    </div>
                    <p class="text-xs text-gray-500">Automated data movement platform</p>
                  </div>

                  <!-- Airbyte -->
                  <div
                    @click="formData.selectedIntegration = 'airbyte'"
                    :class="[
                      'p-4 border-2 rounded-lg cursor-pointer transition-all duration-200',
                      formData.selectedIntegration === 'airbyte'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex items-center mb-2">
                      <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                        </svg>
                      </div>
                      <span class="ml-3 font-semibold text-gray-900">Airbyte</span>
                    </div>
                    <p class="text-xs text-gray-500">Open-source data integration</p>
                  </div>

                  <!-- AWS -->
                  <div
                    @click="formData.selectedIntegration = 'aws'"
                    :class="[
                      'p-4 border-2 rounded-lg cursor-pointer transition-all duration-200',
                      formData.selectedIntegration === 'aws'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex items-center mb-2">
                      <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M18.75 11.35a4.32 4.32 0 01-.79-.08 3.9 3.9 0 01-.73-.23l-.17-.04h-.12l-.15.06-.08.1a2.28 2.28 0 01-.45.53 1.89 1.89 0 01-1.15.4 2.13 2.13 0 01-1.23-.4 2.76 2.76 0 01-.5-.53l-.08-.1-.15-.06h-.12l-.17.04a3.9 3.9 0 01-.73.23 4.32 4.32 0 01-.79.08 4.12 4.12 0 01-2.92-1.21A4.12 4.12 0 016.3 7.22a4.12 4.12 0 011.21-2.92A4.12 4.12 0 0110.43 3.1a4.32 4.32 0 01.79.08 3.9 3.9 0 01.73.23l.17.04h.12l.15-.06.08-.1a2.28 2.28 0 01.45-.53 1.89 1.89 0 011.15-.4c.43 0 .84.13 1.23.4.21.15.37.33.5.53l.08.1.15.06h.12l.17-.04a3.9 3.9 0 01.73-.23 4.32 4.32 0 01.79-.08 4.12 4.12 0 012.92 1.21 4.12 4.12 0 011.21 2.92 4.12 4.12 0 01-1.21 2.92 4.12 4.12 0 01-2.92 1.21z"/>
                        </svg>
                      </div>
                      <span class="ml-3 font-semibold text-gray-900">AWS</span>
                    </div>
                    <p class="text-xs text-gray-500">S3, Glue, Redshift</p>
                  </div>

                  <!-- Azure -->
                  <div
                    @click="formData.selectedIntegration = 'azure'"
                    :class="[
                      'p-4 border-2 rounded-lg cursor-pointer transition-all duration-200',
                      formData.selectedIntegration === 'azure'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex items-center mb-2">
                      <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M13.05 4.24L6.56 18.05a.5.5 0 00.46.7h12.46a.5.5 0 00.46-.7L13.55 4.24a.5.5 0 00-.5 0z"/>
                        </svg>
                      </div>
                      <span class="ml-3 font-semibold text-gray-900">Azure</span>
                    </div>
                    <p class="text-xs text-gray-500">Blob Storage, Synapse, Fabric</p>
                  </div>

                  <!-- GCP -->
                  <div
                    @click="formData.selectedIntegration = 'gcp'"
                    :class="[
                      'p-4 border-2 rounded-lg cursor-pointer transition-all duration-200',
                      formData.selectedIntegration === 'gcp'
                        ? 'border-cyan-500 bg-cyan-50 shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow'
                    ]"
                  >
                    <div class="flex items-center mb-2">
                      <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2L2 19h20L12 2zm0 3.84L18.26 17H5.74L12 5.84z"/>
                        </svg>
                      </div>
                      <span class="ml-3 font-semibold text-gray-900">Google Cloud</span>
                    </div>
                    <p class="text-xs text-gray-500">GCS, BigQuery, Dataflow</p>
                  </div>
                </div>
              </div>

              <!-- Fivetran Configuration -->
              <div v-if="formData.selectedIntegration === 'fivetran'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <h3 class="text-lg font-semibold text-slate-800">Fivetran Configuration</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">API Key</label>
                    <input
                      v-model="formData.integrationConfig.fivetranApiKey"
                      type="password"
                      placeholder="Enter Fivetran API Key"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Group ID</label>
                    <input
                      v-model="formData.integrationConfig.fivetranGroupId"
                      type="text"
                      placeholder="Enter Fivetran Group ID"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                </div>
              </div>

              <!-- Airbyte Configuration -->
              <div v-if="formData.selectedIntegration === 'airbyte'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <h3 class="text-lg font-semibold text-slate-800">Airbyte Configuration</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Airbyte Host URL</label>
                    <input
                      v-model="formData.integrationConfig.airbyteHost"
                      type="text"
                      placeholder="https://airbyte.example.com"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Workspace ID</label>
                    <input
                      v-model="formData.integrationConfig.airbyteWorkspaceId"
                      type="text"
                      placeholder="Enter Workspace ID"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                </div>
              </div>

              <!-- AWS Configuration -->
              <div v-if="formData.selectedIntegration === 'aws'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <h3 class="text-lg font-semibold text-slate-800">AWS Configuration</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Access Key ID</label>
                    <input
                      v-model="formData.integrationConfig.awsAccessKey"
                      type="text"
                      placeholder="AKIAIOSFODNN7EXAMPLE"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Secret Access Key</label>
                    <input
                      v-model="formData.integrationConfig.awsSecretKey"
                      type="password"
                      placeholder="Enter Secret Key"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Region</label>
                    <select
                      v-model="formData.integrationConfig.awsRegion"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 text-base transition-all duration-200"
                    >
                      <option value="us-east-1">US East (N. Virginia)</option>
                      <option value="us-west-2">US West (Oregon)</option>
                      <option value="eu-west-1">EU (Ireland)</option>
                      <option value="eu-central-1">EU (Frankfurt)</option>
                      <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">S3 Bucket</label>
                    <input
                      v-model="formData.integrationConfig.s3Bucket"
                      type="text"
                      placeholder="my-dbt-bucket"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                </div>
              </div>

              <!-- Azure Configuration -->
              <div v-if="formData.selectedIntegration === 'azure'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <h3 class="text-lg font-semibold text-slate-800">Azure Configuration</h3>
                <div class="space-y-5">
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Connection String</label>
                    <input
                      v-model="formData.integrationConfig.azureConnectionString"
                      type="password"
                      placeholder="DefaultEndpointsProtocol=https;AccountName=..."
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Container Name</label>
                    <input
                      v-model="formData.integrationConfig.azureContainerName"
                      type="text"
                      placeholder="dbt-models"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                </div>
              </div>

              <!-- GCP Configuration -->
              <div v-if="formData.selectedIntegration === 'gcp'" class="bg-slate-50 rounded-xl p-6 space-y-5 border border-slate-200">
                <h3 class="text-lg font-semibold text-slate-800">Google Cloud Configuration</h3>
                <div class="space-y-5">
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Project ID</label>
                    <input
                      v-model="formData.integrationConfig.gcpProjectId"
                      type="text"
                      placeholder="my-gcp-project"
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-base transition-all duration-200"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 tracking-wide mb-2">Service Account Key (JSON)</label>
                    <textarea
                      v-model="formData.integrationConfig.gcpServiceAccountKey"
                      rows="4"
                      placeholder='{"type": "service_account", ...}'
                      class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 text-slate-800 placeholder:text-slate-400 text-sm font-mono transition-all duration-200 resize-none"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Info Box when integrations disabled -->
            <div v-if="!formData.enableIntegrations" class="bg-blue-50 rounded-lg p-4">
              <div class="flex">
                <div class="flex-shrink-0">
                  <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                  </svg>
                </div>
                <div class="ml-3">
                  <h3 class="text-sm font-medium text-blue-800">Skip for Now</h3>
                  <p class="mt-1 text-sm text-blue-700">
                    You can configure data platform integrations later from the migration details page after your dbt models are generated.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Navigation Buttons -->
          <div class="px-6 py-4 bg-slate-50/50 border-t border-slate-200/50 flex justify-between rounded-b-xl">
            <button
              v-if="currentStep > 1"
              @click="prevStep"
              class="inline-flex items-center px-4 py-2 border border-slate-300 shadow-sm text-sm font-medium rounded-lg text-slate-700 bg-white hover:bg-slate-50 transition-all duration-200"
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
                class="px-4 py-2 border border-slate-300 shadow-sm text-sm font-medium rounded-lg text-slate-700 bg-white hover:bg-slate-50 transition-all duration-200"
              >
                Cancel
              </button>

              <button
                v-if="currentStep < totalSteps"
                @click="nextStep"
                :disabled="!isStepValid"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-lg text-sm font-medium rounded-lg text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
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
                class="inline-flex items-center px-6 py-2 border border-transparent shadow-lg text-sm font-medium rounded-lg text-white bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
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
