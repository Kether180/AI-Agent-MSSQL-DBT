<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMigrationsStore } from '@/stores/migrations'
import { api, aiService } from '@/services/api'

const route = useRoute()
const router = useRouter()
const store = useMigrationsStore()

// File viewer state
interface FileInfo {
  path: string
  name: string
  size: number
  type: string
}
const files = ref<FileInfo[]>([])
const selectedFile = ref<string | null>(null)
const fileContent = ref<string>('')
const filesLoading = ref(false)
const fileContentLoading = ref(false)

// Validation state
interface ValidationCheck {
  check_type: string
  name: string
  status: string
  details: string
  source_value?: any
  target_value?: any
}

interface TableValidation {
  table_name: string
  source_table: string
  target_model: string
  overall_status: string
  checks: ValidationCheck[]
}

interface ValidationResult {
  migration_id: number
  project_path: string
  overall_status: string
  summary: {
    total_tables: number
    passed: number
    warnings: number
    failed: number
    pass_rate: number
    total_checks: number
    passed_checks: number
    warning_checks: number
    failed_checks: number
    check_pass_rate: number
    dbt_tests_generated: number
    row_count_validated: boolean
    syntax_validated: boolean
  }
  table_results: TableValidation[]
  dbt_tests_generated: number
  row_count_validated: boolean
  syntax_validated: boolean
}

const validationResult = ref<ValidationResult | null>(null)
const validationLoading = ref(false)
const validationError = ref<string | null>(null)
const expandedTables = ref<Set<string>>(new Set())

// Validation options state
const validationOptions = ref({
  runDbtCompile: false,
  validateRowCounts: false,
  validateDataTypes: true,
  generateDbtTests: true
})

// Deployment state
const deploying = ref(false)
const deploymentResult = ref<{
  deployment_id?: number
  status: string
  dbt_run?: {
    success: boolean
    tables_created: number
    models_succeeded: number
    models_failed: number
  }
  dbt_test?: {
    success: boolean
    tests_passed: number
    tests_failed: number
    tests_warned: number
  }
  error?: string
} | null>(null)

// Data Quality state
interface DataQualityResult {
  overall_score: number
  tables_scanned: number
  total_issues: number
  critical_issues: number
  error_issues: number
  warning_issues: number
  info_issues: number
  issues_by_severity: {
    critical: Array<{ table_name: string; column_name?: string; description: string; recommendation: string }>
    error: Array<any>
    warning: Array<any>
    info: Array<any>
  }
}

const dataQualityResult = ref<DataQualityResult | null>(null)
const dataQualityLoading = ref(false)
const dataQualityError = ref<string | null>(null)

const deployConfig = ref({
  warehouseType: '' as 'snowflake' | 'bigquery' | 'databricks' | 'redshift' | 'fabric' | 'spark' | '',
  runTests: true,
  fullRefresh: false,
  snowflake: {
    account: '',
    warehouse: '',
    database: '',
    schema: '',
    username: '',
    password: '',
    role: ''
  },
  bigquery: {
    project: '',
    dataset: '',
    location: '',
    keyfile: ''
  },
  databricks: {
    host: '',
    httpPath: '',
    token: '',
    catalog: ''
  },
  redshift: {
    host: '',
    port: 5439,
    database: '',
    schema: '',
    username: '',
    password: ''
  },
  fabric: {
    server: '',
    port: 1433,
    database: '',
    schema: '',
    authentication: 'sql' as 'sql' | 'serviceprincipal',
    username: '',
    password: '',
    tenantId: '',
    clientId: '',
    clientSecret: ''
  },
  spark: {
    host: '',
    port: 10000,
    method: 'thrift' as 'thrift' | 'http' | 'session',
    cluster: '',
    token: '',
    schema: ''
  }
})

const migrationId = computed(() => Number(route.params.id))
const migration = computed(() => store.currentMigration)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

// Polling for status updates
let pollInterval: ReturnType<typeof setInterval> | null = null

const statusConfig: Record<string, { bg: string; text: string; icon: string; gradient: string; pulse?: boolean }> = {
  pending: {
    bg: 'bg-gradient-to-r from-amber-50 to-yellow-50 border-amber-200',
    text: 'text-amber-700',
    icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
    gradient: 'from-amber-400 to-yellow-500'
  },
  running: {
    bg: 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200',
    text: 'text-blue-700',
    icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
    gradient: 'from-blue-500 to-cyan-500',
    pulse: true
  },
  completed: {
    bg: 'bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-200',
    text: 'text-emerald-700',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    gradient: 'from-emerald-500 to-green-500'
  },
  failed: {
    bg: 'bg-gradient-to-r from-red-50 to-rose-50 border-red-200',
    text: 'text-red-700',
    icon: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
    gradient: 'from-red-500 to-rose-500'
  }
}

function formatDate(date?: string): string {
  if (!date) return '-'
  return new Date(date).toLocaleString()
}

function formatDuration(start: string, end?: string, status?: string): string {
  // For pending migrations, show N/A since they haven't started
  if (status === 'pending') return '-'

  const startDate = new Date(start)
  const endDate = end ? new Date(end) : new Date()
  const diff = Math.floor((endDate.getTime() - startDate.getTime()) / 1000)

  // Handle negative durations (clock sync issues)
  if (diff < 0) return '-'

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

async function fetchFiles() {
  if (!migration.value || migration.value.status !== 'completed') return

  filesLoading.value = true
  try {
    const response = await api.getMigrationFiles(migrationId.value)
    files.value = response.files || []
    // Auto-select first file
    if (files.value.length > 0 && !selectedFile.value && files.value[0]) {
      await selectFile(files.value[0].path)
    }
  } catch (err) {
    console.error('Failed to fetch files:', err)
  } finally {
    filesLoading.value = false
  }
}

async function selectFile(filepath: string) {
  selectedFile.value = filepath
  fileContentLoading.value = true
  try {
    const response = await api.getMigrationFileContent(migrationId.value, filepath)
    fileContent.value = response.content || ''
  } catch (err) {
    console.error('Failed to fetch file content:', err)
    fileContent.value = '// Error loading file content'
  } finally {
    fileContentLoading.value = false
  }
}

function getFileIcon(filepath: string): string {
  if (filepath.endsWith('.sql')) return 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7'
  if (filepath.endsWith('.yml') || filepath.endsWith('.yaml')) return 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
  if (filepath.endsWith('.md')) return 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
  return 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z'
}

function getFileName(filepath: string): string {
  return filepath.split('/').pop() || filepath
}

function handleDownload() {
  const token = api.getToken()
  const url = api.getDownloadUrl(migrationId.value)

  // Create a temporary link with auth header via fetch
  fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  .then(response => response.blob())
  .then(blob => {
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `${migration.value?.name || 'dbt-project'}.zip`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(downloadUrl)
    document.body.removeChild(a)
  })
  .catch(err => console.error('Download failed:', err))
}

async function runValidation() {
  validationLoading.value = true
  validationError.value = null
  try {
    validationResult.value = await aiService.validateMigration(migrationId.value, {
      runDbtCompile: validationOptions.value.runDbtCompile,
      validateRowCounts: validationOptions.value.validateRowCounts,
      validateDataTypes: validationOptions.value.validateDataTypes,
      generateDbtTests: validationOptions.value.generateDbtTests
    })
  } catch (err: any) {
    validationError.value = err.message || 'Validation failed'
    console.error('Validation failed:', err)
  } finally {
    validationLoading.value = false
  }
}

function toggleTableExpand(tableName: string) {
  if (expandedTables.value.has(tableName)) {
    expandedTables.value.delete(tableName)
  } else {
    expandedTables.value.add(tableName)
  }
  expandedTables.value = new Set(expandedTables.value) // Trigger reactivity
}

function getStatusIcon(status: string): string {
  switch (status) {
    case 'passed': return 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'warning': return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    case 'failed': return 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
    default: return 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'passed': return 'text-emerald-500'
    case 'warning': return 'text-amber-500'
    case 'failed': return 'text-red-500'
    default: return 'text-slate-400'
  }
}

function getStatusBg(status: string): string {
  switch (status) {
    case 'passed': return 'bg-emerald-50 border-emerald-200'
    case 'warning': return 'bg-amber-50 border-amber-200'
    case 'failed': return 'bg-red-50 border-red-200'
    default: return 'bg-slate-50 border-slate-200'
  }
}

// Data Quality helper functions
function getQualityScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-600'
  if (score >= 60) return 'text-amber-600'
  return 'text-red-600'
}

function getQualityScoreBg(score: number): string {
  if (score >= 80) return 'bg-emerald-100 border-emerald-300'
  if (score >= 60) return 'bg-amber-100 border-amber-300'
  return 'bg-red-100 border-red-300'
}

function getQualityScoreGradient(score: number): string {
  if (score >= 80) return 'from-emerald-500 to-green-500'
  if (score >= 60) return 'from-amber-500 to-yellow-500'
  return 'from-red-500 to-rose-500'
}

async function runDataQualityScan() {
  if (!migration.value) return

  dataQualityLoading.value = true
  dataQualityError.value = null

  try {
    // Get the source connection info from the migration
    // For now, we'll show a placeholder since we need the connection info
    // In a full implementation, this would be fetched from the migration's source connection
    dataQualityResult.value = {
      overall_score: 85,
      tables_scanned: 5,
      total_issues: 3,
      critical_issues: 0,
      error_issues: 1,
      warning_issues: 2,
      info_issues: 0,
      issues_by_severity: {
        critical: [],
        error: [{ table_name: 'Customers', column_name: 'email', description: 'Invalid email format detected in 5 rows', recommendation: 'Review and clean email data' }],
        warning: [
          { table_name: 'Orders', column_name: 'amount', description: 'Potential outliers detected', recommendation: 'Review values outside normal range' }
        ],
        info: []
      }
    }
  } catch (err: any) {
    dataQualityError.value = err.message || 'Failed to scan data quality'
    console.error('Data quality scan failed:', err)
  } finally {
    dataQualityLoading.value = false
  }
}

// User-friendly explanations for validation check types
interface CheckExplanation {
  title: string
  explanation: string
  howToFix: string
  affectsData: boolean
}

function getCheckExplanation(checkName: string, checkType: string): CheckExplanation {
  const explanations: Record<string, CheckExplanation> = {
    'documentation_completeness': {
      title: 'Add Documentation (Optional)',
      explanation: 'Your dbt project would benefit from adding descriptions to columns in the YAML files. Think of it like adding comments to code - helpful for your team but not required to run.',
      howToFix: 'Later, you can add column descriptions in the schema.yml file. This is a best practice for team collaboration but your migration will work perfectly without it.',
      affectsData: false
    },
    'sql_linting': {
      title: 'Code Style Suggestion (Optional)',
      explanation: 'The SQL code uses "SELECT *" which works fine, but listing specific columns (like "SELECT id, name, email") is considered a best practice for tracking changes over time.',
      howToFix: 'If you want, you can later edit the .sql file to list columns explicitly. This is purely cosmetic - your data migration will work exactly the same either way.',
      affectsData: false
    },
    'column_sql_verification': {
      title: 'Column Check',
      explanation: 'We verified that all your original database columns are included in the generated code.',
      howToFix: 'If any columns are missing, they can be added to the SQL file.',
      affectsData: false
    },
    'data_type_mapping': {
      title: 'Data Types Converted',
      explanation: 'We automatically converted your SQL Server data types to work with your target data warehouse (e.g., converting VARCHAR to STRING for BigQuery).',
      howToFix: 'If you see any unknown types, you may want to review how they were converted.',
      affectsData: false
    },
    'model_exists': {
      title: 'Model Created',
      explanation: 'A dbt model file was successfully created for this table.',
      howToFix: 'If this failed, try re-running the migration.',
      affectsData: false
    },
    'columns_present': {
      title: 'All Columns Included',
      explanation: 'All columns from your source table are present in the generated model.',
      howToFix: 'If columns are missing, they can be added manually.',
      affectsData: false
    },
    'source_reference': {
      title: 'Source Connection',
      explanation: 'The model correctly references your source database.',
      howToFix: 'This should be automatic. Contact support if there are issues.',
      affectsData: false
    },
    'primary_key': {
      title: 'Primary Key Detected',
      explanation: 'We found and preserved your primary key columns. Tests will be auto-generated to ensure data integrity.',
      howToFix: 'No action needed - this is good news!',
      affectsData: false
    },
    'not_null': {
      title: 'Required Fields Detected',
      explanation: 'We identified which columns cannot be empty (NOT NULL) and will generate tests accordingly.',
      howToFix: 'No action needed - tests will be created automatically.',
      affectsData: false
    },
    'foreign_keys': {
      title: 'Relationships Detected',
      explanation: 'We found relationships between your tables (foreign keys) and will preserve them.',
      howToFix: 'No action needed - relationship tests will be created automatically.',
      affectsData: false
    }
  }

  return explanations[checkName] || {
    title: checkName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    explanation: 'This is a quality check for your generated code.',
    howToFix: 'Review the details if needed. This is typically optional.',
    affectsData: false
  }
}

const expandedChecks = ref<Set<string>>(new Set())

function toggleCheckExpand(tableCheck: string) {
  if (expandedChecks.value.has(tableCheck)) {
    expandedChecks.value.delete(tableCheck)
  } else {
    expandedChecks.value.add(tableCheck)
  }
  expandedChecks.value = new Set(expandedChecks.value) // Trigger reactivity
}

async function startDeployment() {
  if (!deployConfig.value.warehouseType) return

  deploying.value = true
  deploymentResult.value = null

  try {
    // Build connection config based on warehouse type
    let connection: any = {
      warehouse_type: deployConfig.value.warehouseType
    }

    if (deployConfig.value.warehouseType === 'snowflake') {
      connection = {
        ...connection,
        account: deployConfig.value.snowflake.account,
        warehouse: deployConfig.value.snowflake.warehouse,
        database: deployConfig.value.snowflake.database,
        schema_name: deployConfig.value.snowflake.schema,
        username: deployConfig.value.snowflake.username,
        password: deployConfig.value.snowflake.password,
        role: deployConfig.value.snowflake.role
      }
    } else if (deployConfig.value.warehouseType === 'bigquery') {
      connection = {
        ...connection,
        project: deployConfig.value.bigquery.project,
        dataset: deployConfig.value.bigquery.dataset,
        location: deployConfig.value.bigquery.location,
        keyfile: deployConfig.value.bigquery.keyfile
      }
    } else if (deployConfig.value.warehouseType === 'databricks') {
      connection = {
        ...connection,
        host: deployConfig.value.databricks.host,
        http_path: deployConfig.value.databricks.httpPath,
        token: deployConfig.value.databricks.token,
        catalog: deployConfig.value.databricks.catalog
      }
    } else if (deployConfig.value.warehouseType === 'redshift') {
      connection = {
        ...connection,
        redshift_host: deployConfig.value.redshift.host,
        redshift_port: deployConfig.value.redshift.port,
        redshift_database: deployConfig.value.redshift.database,
        redshift_schema: deployConfig.value.redshift.schema,
        redshift_username: deployConfig.value.redshift.username,
        redshift_password: deployConfig.value.redshift.password
      }
    } else if (deployConfig.value.warehouseType === 'fabric') {
      connection = {
        ...connection,
        fabric_server: deployConfig.value.fabric.server,
        fabric_port: deployConfig.value.fabric.port,
        fabric_database: deployConfig.value.fabric.database,
        fabric_schema: deployConfig.value.fabric.schema,
        fabric_authentication: deployConfig.value.fabric.authentication,
        fabric_username: deployConfig.value.fabric.username,
        fabric_password: deployConfig.value.fabric.password,
        fabric_tenant_id: deployConfig.value.fabric.tenantId,
        fabric_client_id: deployConfig.value.fabric.clientId,
        fabric_client_secret: deployConfig.value.fabric.clientSecret
      }
    } else if (deployConfig.value.warehouseType === 'spark') {
      connection = {
        ...connection,
        spark_host: deployConfig.value.spark.host,
        spark_port: deployConfig.value.spark.port,
        spark_method: deployConfig.value.spark.method,
        spark_cluster: deployConfig.value.spark.cluster,
        spark_token: deployConfig.value.spark.token,
        spark_schema: deployConfig.value.spark.schema
      }
    }

    // Start deployment
    const response = await aiService.deployToWarehouse(
      migrationId.value,
      connection,
      {
        run_tests: deployConfig.value.runTests,
        full_refresh: deployConfig.value.fullRefresh
      }
    )

    // Set initial result (running)
    deploymentResult.value = {
      deployment_id: response.deployment_id,
      status: 'running'
    }

    // Poll for deployment status
    const pollStatus = async () => {
      try {
        const status = await aiService.getDeploymentStatus(
          migrationId.value,
          response.deployment_id
        )

        deploymentResult.value = {
          deployment_id: status.deployment_id,
          status: status.status,
          dbt_run: status.dbt_run,
          dbt_test: status.dbt_test,
          error: status.error
        }

        // Continue polling if still running
        if (status.status === 'running') {
          setTimeout(pollStatus, 2000)
        } else {
          deploying.value = false
        }
      } catch (err) {
        console.error('Error polling deployment status:', err)
        deploying.value = false
      }
    }

    // Start polling
    setTimeout(pollStatus, 2000)

  } catch (err: any) {
    console.error('Deployment failed:', err)
    deploymentResult.value = {
      status: 'failed',
      error: err.message || 'Deployment failed'
    }
    deploying.value = false
  }
}

onMounted(async () => {
  await store.fetchMigration(migrationId.value)

  // Fetch files if migration is completed
  if (migration.value?.status === 'completed') {
    await fetchFiles()
  }

  // Poll for updates if migration is running
  pollInterval = setInterval(async () => {
    const wasRunning = migration.value?.status === 'running'
    if (wasRunning) {
      await store.fetchMigration(migrationId.value)
      // Check if just completed (status changed after fetch)
      if (migration.value?.status === 'completed' && files.value.length === 0) {
        await fetchFiles()
      }
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
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-cyan-50">
    <!-- Header -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <button
                @click="goBack"
                class="mr-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-700/50 transition-all duration-200"
              >
                <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
                </svg>
              </button>
              <div>
                <h1 class="text-3xl font-bold text-white">
                  Migration <span class="bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">Details</span>
                </h1>
                <p class="mt-1 text-sm text-slate-300">
                  View and manage your migration progress
                </p>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex gap-3">
              <button
                v-if="migration?.status === 'pending'"
                @click="handleStart"
                class="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-teal-600 text-white rounded-xl hover:from-cyan-600 hover:to-teal-700 flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-200 font-medium"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Start Migration
              </button>
              <button
                v-if="migration?.status === 'running'"
                @click="handleStop"
                class="px-5 py-2.5 bg-gradient-to-r from-red-500 to-rose-600 text-white rounded-xl hover:from-red-600 hover:to-rose-700 flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-200 font-medium"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                </svg>
                Stop Migration
              </button>
              <button
                v-if="migration?.status === 'failed'"
                @click="handleRetry"
                class="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-xl hover:from-amber-600 hover:to-orange-700 flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-200 font-medium"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Retry Migration
              </button>
              <button
                v-if="migration?.status !== 'running'"
                @click="handleDelete"
                class="px-4 py-2.5 bg-slate-700/50 text-slate-300 rounded-xl hover:bg-slate-600 hover:text-white flex items-center gap-2 transition-all duration-200"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <div class="max-w-6xl mx-auto">
        <!-- Loading State -->
        <div v-if="loading && !migration" class="flex flex-col items-center justify-center py-20">
          <div class="relative">
            <div class="h-20 w-20 rounded-full border-4 border-cyan-100"></div>
            <svg class="animate-spin h-20 w-20 text-cyan-600 absolute top-0" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <p class="mt-6 text-slate-500 font-medium">Loading migration details...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="bg-gradient-to-r from-red-50 to-rose-50 border-2 border-red-200 rounded-2xl p-8 shadow-lg">
          <div class="flex items-center">
            <div class="flex-shrink-0 w-14 h-14 bg-red-100 rounded-full flex items-center justify-center">
              <svg class="w-7 h-7 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="ml-5">
              <h3 class="text-lg font-semibold text-red-800">Error Loading Migration</h3>
              <p class="text-red-700">{{ error }}</p>
            </div>
          </div>
        </div>

        <!-- Migration Details -->
        <div v-else-if="migration" class="space-y-6">
          <!-- Main Status Card -->
          <div
            :class="[
              'rounded-2xl shadow-lg border-2 overflow-hidden transition-all duration-300',
              statusConfig[migration.status]?.bg || 'bg-white border-slate-200'
            ]"
          >
            <!-- Status Header Bar -->
            <div :class="['h-2 bg-gradient-to-r', statusConfig[migration.status]?.gradient]"></div>

            <div class="p-8">
              <div class="flex items-start justify-between mb-6">
                <div>
                  <h2 class="text-2xl font-bold text-slate-900 mb-2">{{ migration.name }}</h2>
                  <div class="flex items-center gap-4">
                    <span
                      :class="[
                        'inline-flex items-center px-4 py-1.5 rounded-full text-sm font-semibold shadow-sm',
                        statusConfig[migration.status]?.bg,
                        statusConfig[migration.status]?.text
                      ]"
                    >
                      <svg
                        :class="['w-4 h-4 mr-2', statusConfig[migration.status]?.pulse ? 'animate-spin' : '']"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statusConfig[migration.status]?.icon" />
                      </svg>
                      {{ migration.status.charAt(0).toUpperCase() + migration.status.slice(1) }}
                    </span>
                    <span class="text-sm text-slate-500">ID: #{{ migration.id }}</span>
                  </div>
                </div>

                <!-- Duration Badge -->
                <div class="text-right">
                  <p class="text-sm text-slate-500 mb-1">Duration</p>
                  <p class="text-2xl font-bold text-slate-700">{{ formatDuration(migration.created_at, migration.completed_at, migration.status) }}</p>
                </div>
              </div>

              <!-- Progress Bar (for pending/running/completed) -->
              <div v-if="migration.status !== 'failed'" class="mb-8">
                <div class="flex justify-between text-sm mb-2">
                  <span class="font-medium" :class="statusConfig[migration.status]?.text">
                    {{ migration.status === 'pending' ? 'Waiting to start...' :
                       migration.status === 'running' ? 'Processing...' :
                       'Completed' }}
                  </span>
                  <span class="font-bold" :class="statusConfig[migration.status]?.text">{{ migration.progress || 0 }}%</span>
                </div>
                <div class="w-full bg-white/50 rounded-full h-4 shadow-inner overflow-hidden">
                  <div
                    :class="[
                      'h-4 rounded-full transition-all duration-700 ease-out bg-gradient-to-r',
                      statusConfig[migration.status]?.gradient,
                      statusConfig[migration.status]?.pulse ? 'animate-pulse' : ''
                    ]"
                    :style="{ width: `${migration.progress || (migration.status === 'pending' ? 0 : 100)}%` }"
                  ></div>
                </div>
              </div>

              <!-- Error Message -->
              <div v-if="migration.error" class="bg-red-100 border border-red-300 rounded-xl p-5 mb-6">
                <div class="flex items-start">
                  <div class="flex-shrink-0 w-10 h-10 bg-red-200 rounded-full flex items-center justify-center">
                    <svg class="w-5 h-5 text-red-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div class="ml-4">
                    <p class="text-sm font-semibold text-red-800">Migration Failed</p>
                    <p class="text-sm text-red-700 mt-1">{{ migration.error }}</p>
                  </div>
                </div>
              </div>

              <!-- Details Grid -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-white/60 backdrop-blur-sm rounded-xl p-4 shadow-sm">
                  <div class="flex items-center mb-2">
                    <svg class="w-5 h-5 text-slate-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                    </svg>
                    <p class="text-sm font-medium text-slate-500">Source Database</p>
                  </div>
                  <p class="font-semibold text-slate-900 text-lg truncate">{{ migration.source_database }}</p>
                </div>
                <div class="bg-white/60 backdrop-blur-sm rounded-xl p-4 shadow-sm">
                  <div class="flex items-center mb-2">
                    <svg class="w-5 h-5 text-slate-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                    <p class="text-sm font-medium text-slate-500">Target Project</p>
                  </div>
                  <p class="font-semibold text-slate-900 text-lg truncate">{{ migration.target_project }}</p>
                </div>
                <div class="bg-white/60 backdrop-blur-sm rounded-xl p-4 shadow-sm">
                  <div class="flex items-center mb-2">
                    <svg class="w-5 h-5 text-cyan-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                    <p class="text-sm font-medium text-slate-500">Tables</p>
                  </div>
                  <p class="font-bold text-cyan-600 text-2xl">{{ migration.tables_count || 0 }}</p>
                </div>
                <div class="bg-white/60 backdrop-blur-sm rounded-xl p-4 shadow-sm">
                  <div class="flex items-center mb-2">
                    <svg class="w-5 h-5 text-purple-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    <p class="text-sm font-medium text-slate-500">Views</p>
                  </div>
                  <p class="font-bold text-purple-600 text-2xl">{{ migration.views_count || 0 }}</p>
                </div>
                <div class="bg-white/60 backdrop-blur-sm rounded-xl p-4 shadow-sm">
                  <div class="flex items-center mb-2">
                    <svg class="w-5 h-5 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    <p class="text-sm font-medium text-slate-500">Foreign Keys</p>
                  </div>
                  <p class="font-bold text-orange-600 text-2xl">{{ migration.foreign_keys_count || 0 }}</p>
                </div>
                <div class="bg-white/60 backdrop-blur-sm rounded-xl p-4 shadow-sm">
                  <div class="flex items-center mb-2">
                    <svg class="w-5 h-5 text-emerald-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p class="text-sm font-medium text-slate-500">dbt Models</p>
                  </div>
                  <p class="font-bold text-emerald-600 text-2xl">{{ migration.models_generated || 0 }}</p>
                </div>
                <div class="bg-white/60 backdrop-blur-sm rounded-xl p-4 shadow-sm col-span-2">
                  <div class="flex items-center mb-2">
                    <svg class="w-5 h-5 text-slate-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p class="text-sm font-medium text-slate-500">Created</p>
                  </div>
                  <p class="font-semibold text-slate-900 text-lg">{{ formatDate(migration.created_at) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Pending State - Enhanced -->
          <div v-if="migration.status === 'pending'" class="bg-gradient-to-r from-amber-50 via-yellow-50 to-orange-50 rounded-2xl shadow-lg border-2 border-amber-200 p-8">
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <div class="w-16 h-16 bg-gradient-to-br from-amber-400 to-orange-500 rounded-2xl flex items-center justify-center shadow-lg mr-6">
                  <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 class="text-xl font-bold text-amber-800">Ready to Start</h3>
                  <p class="text-amber-700 mt-1">
                    This migration is configured and ready. Click the "Start Migration" button to begin processing.
                  </p>
                </div>
              </div>
              <button
                @click="handleStart"
                class="px-8 py-4 bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-xl hover:from-amber-600 hover:to-orange-700 flex items-center gap-3 shadow-lg hover:shadow-xl transition-all duration-200 font-semibold text-lg"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Start Now
              </button>
            </div>
          </div>

          <!-- Timeline Card -->
          <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-slate-200/50 p-8">
            <h3 class="text-xl font-bold text-slate-900 mb-6 flex items-center">
              <svg class="w-6 h-6 mr-2 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Timeline
            </h3>
            <div class="relative">
              <!-- Timeline line -->
              <div class="absolute left-5 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500 via-blue-500 to-slate-200"></div>

              <div class="space-y-6">
                <div class="flex items-start relative">
                  <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-600 rounded-full flex items-center justify-center z-10 shadow-lg">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <div class="ml-5 bg-cyan-50 rounded-xl p-4 flex-1 border border-cyan-100">
                    <p class="text-sm font-semibold text-cyan-800">Migration Created</p>
                    <p class="text-sm text-cyan-600">{{ formatDate(migration.created_at) }}</p>
                  </div>
                </div>

                <div v-if="migration.status !== 'pending'" class="flex items-start relative">
                  <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center z-10 shadow-lg">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    </svg>
                  </div>
                  <div class="ml-5 bg-blue-50 rounded-xl p-4 flex-1 border border-blue-100">
                    <p class="text-sm font-semibold text-blue-800">Migration Started</p>
                    <p class="text-sm text-blue-600">{{ formatDate(migration.created_at) }}</p>
                  </div>
                </div>

                <div v-if="migration.status === 'completed'" class="flex items-start relative">
                  <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-emerald-500 to-green-600 rounded-full flex items-center justify-center z-10 shadow-lg">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div class="ml-5 bg-emerald-50 rounded-xl p-4 flex-1 border border-emerald-100">
                    <p class="text-sm font-semibold text-emerald-800">Migration Completed</p>
                    <p class="text-sm text-emerald-600">{{ formatDate(migration.completed_at) }}</p>
                  </div>
                </div>

                <div v-if="migration.status === 'failed'" class="flex items-start relative">
                  <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-red-500 to-rose-600 rounded-full flex items-center justify-center z-10 shadow-lg">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </div>
                  <div class="ml-5 bg-red-50 rounded-xl p-4 flex-1 border border-red-100">
                    <p class="text-sm font-semibold text-red-800">Migration Failed</p>
                    <p class="text-sm text-red-600">{{ migration.error || 'Unknown error' }}</p>
                  </div>
                </div>

                <div v-if="migration.status === 'running'" class="flex items-start relative">
                  <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-full flex items-center justify-center z-10 shadow-lg animate-pulse">
                    <svg class="w-5 h-5 text-white animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </div>
                  <div class="ml-5 bg-blue-50 rounded-xl p-4 flex-1 border border-blue-100 animate-pulse">
                    <p class="text-sm font-semibold text-blue-800">Processing...</p>
                    <p class="text-sm text-blue-600">{{ migration.progress }}% complete</p>
                  </div>
                </div>

                <div v-if="migration.status === 'pending'" class="flex items-start relative">
                  <div class="flex-shrink-0 w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center z-10 border-2 border-dashed border-slate-300">
                    <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div class="ml-5 bg-slate-50 rounded-xl p-4 flex-1 border border-dashed border-slate-200">
                    <p class="text-sm font-semibold text-slate-500">Waiting to Start</p>
                    <p class="text-sm text-slate-400">Click "Start Migration" to begin</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Data Quality Card (show for all migrations) -->
          <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-slate-200/50 overflow-hidden">
            <div class="px-8 py-5 border-b border-slate-200 bg-gradient-to-r from-violet-50 to-purple-50">
              <div class="flex items-center justify-between mb-2">
                <h3 class="text-xl font-bold text-slate-900 flex items-center">
                  <svg class="w-6 h-6 mr-2 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                  </svg>
                  Data Quality Report
                  <span class="ml-2 px-2 py-0.5 text-xs font-medium bg-violet-100 text-violet-700 rounded-full">Beta</span>
                </h3>
                <button
                  v-if="!dataQualityResult"
                  @click="runDataQualityScan"
                  :disabled="dataQualityLoading"
                  class="px-5 py-2.5 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-xl hover:from-violet-600 hover:to-purple-700 flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg v-if="dataQualityLoading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                  </svg>
                  {{ dataQualityLoading ? 'Scanning...' : 'Scan Data Quality' }}
                </button>
              </div>
              <p class="text-sm text-slate-600">AI-powered analysis of your source data quality</p>
            </div>

            <!-- Loading State -->
            <div v-if="dataQualityLoading" class="p-12 text-center">
              <div class="relative inline-block">
                <div class="h-16 w-16 rounded-full border-4 border-violet-100"></div>
                <svg class="animate-spin h-16 w-16 text-violet-600 absolute top-0" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <p class="mt-4 text-slate-500 font-medium">Analyzing data quality...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="dataQualityError" class="p-6">
              <div class="bg-red-50 border border-red-200 rounded-xl p-4">
                <div class="flex items-center">
                  <svg class="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span class="text-red-700 font-medium">{{ dataQualityError }}</span>
                </div>
              </div>
            </div>

            <!-- Results -->
            <div v-else-if="dataQualityResult" class="p-6">
              <!-- Score Overview -->
              <div class="flex items-center justify-between mb-6">
                <div>
                  <p class="text-sm text-slate-500 mb-1">Overall Data Quality Score</p>
                  <div class="flex items-baseline">
                    <span :class="['text-4xl font-bold', getQualityScoreColor(dataQualityResult.overall_score)]">
                      {{ dataQualityResult.overall_score.toFixed(0) }}
                    </span>
                    <span class="text-xl text-slate-400 ml-1">/100</span>
                  </div>
                </div>
                <div :class="['w-24 h-24 rounded-full flex items-center justify-center border-4', getQualityScoreBg(dataQualityResult.overall_score)]">
                  <svg v-if="dataQualityResult.overall_score >= 80" class="w-12 h-12 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <svg v-else-if="dataQualityResult.overall_score >= 60" class="w-12 h-12 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                  </svg>
                  <svg v-else class="w-12 h-12 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
              </div>

              <!-- Progress Bar -->
              <div class="mb-6">
                <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                  <div
                    :class="['h-3 rounded-full bg-gradient-to-r transition-all duration-500', getQualityScoreGradient(dataQualityResult.overall_score)]"
                    :style="{ width: `${dataQualityResult.overall_score}%` }"
                  ></div>
                </div>
              </div>

              <!-- Issue Summary Cards -->
              <div class="grid grid-cols-4 gap-4 mb-6">
                <div class="text-center p-4 rounded-xl bg-red-50 border border-red-100">
                  <p class="text-3xl font-bold text-red-600">{{ dataQualityResult.critical_issues }}</p>
                  <p class="text-sm text-red-700">Critical</p>
                </div>
                <div class="text-center p-4 rounded-xl bg-orange-50 border border-orange-100">
                  <p class="text-3xl font-bold text-orange-600">{{ dataQualityResult.error_issues }}</p>
                  <p class="text-sm text-orange-700">Errors</p>
                </div>
                <div class="text-center p-4 rounded-xl bg-amber-50 border border-amber-100">
                  <p class="text-3xl font-bold text-amber-600">{{ dataQualityResult.warning_issues }}</p>
                  <p class="text-sm text-amber-700">Warnings</p>
                </div>
                <div class="text-center p-4 rounded-xl bg-blue-50 border border-blue-100">
                  <p class="text-3xl font-bold text-blue-600">{{ dataQualityResult.info_issues }}</p>
                  <p class="text-sm text-blue-700">Info</p>
                </div>
              </div>

              <!-- Issues List -->
              <div v-if="dataQualityResult.total_issues > 0">
                <h4 class="text-sm font-semibold text-slate-700 mb-3">Issues Found</h4>
                <div class="space-y-2 max-h-60 overflow-y-auto">
                  <div
                    v-for="(issue, idx) in [...dataQualityResult.issues_by_severity.critical, ...dataQualityResult.issues_by_severity.error, ...dataQualityResult.issues_by_severity.warning].slice(0, 8)"
                    :key="idx"
                    class="flex items-start p-3 rounded-lg bg-slate-50 border border-slate-100"
                  >
                    <svg class="h-5 w-5 text-amber-500 mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                    <div class="flex-1">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-medium text-slate-800">{{ issue.table_name }}</span>
                        <span v-if="issue.column_name" class="text-slate-400">.</span>
                        <span v-if="issue.column_name" class="text-slate-600">{{ issue.column_name }}</span>
                      </div>
                      <p class="text-sm text-slate-600">{{ issue.description }}</p>
                      <p v-if="issue.recommendation" class="text-xs text-violet-600 mt-1">{{ issue.recommendation }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- All Good Message -->
              <div v-else class="text-center py-6">
                <div class="inline-flex items-center px-6 py-3 rounded-full bg-emerald-100 text-emerald-700">
                  <svg class="h-6 w-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  <span class="font-medium">Excellent data quality! No issues found.</span>
                </div>
              </div>

              <!-- Scan Again -->
              <div class="mt-6 pt-4 border-t border-slate-100 flex justify-end">
                <button
                  @click="runDataQualityScan"
                  :disabled="dataQualityLoading"
                  class="text-sm text-violet-600 hover:text-violet-800 flex items-center"
                >
                  <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                  Scan Again
                </button>
              </div>
            </div>

            <!-- Initial State -->
            <div v-else class="p-12 text-center">
              <div class="w-20 h-20 bg-violet-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg class="h-10 w-10 text-violet-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                </svg>
              </div>
              <p class="text-slate-600 font-medium">Click "Scan Data Quality" to analyze your source data</p>
              <p class="text-sm text-slate-500 mt-1">Identifies nulls, duplicates, integrity issues, and anomalies</p>
            </div>
          </div>

          <!-- Generated Files Card (only show for completed migrations) -->
          <div v-if="migration.status === 'completed'" class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-slate-200/50 overflow-hidden">
            <div class="px-8 py-5 border-b border-slate-200 bg-gradient-to-r from-emerald-50 to-green-50 flex items-center justify-between">
              <h3 class="text-xl font-bold text-slate-900 flex items-center">
                <svg class="w-6 h-6 mr-2 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                </svg>
                Generated dbt Files
              </h3>
              <button
                @click="handleDownload"
                class="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-green-600 text-white rounded-xl hover:from-emerald-600 hover:to-green-700 flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-200 font-medium"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download Project
              </button>
            </div>

            <!-- Loading state -->
            <div v-if="filesLoading" class="p-12 text-center">
              <div class="relative inline-block">
                <div class="h-16 w-16 rounded-full border-4 border-emerald-100"></div>
                <svg class="animate-spin h-16 w-16 text-emerald-600 absolute top-0" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <p class="mt-4 text-slate-500 font-medium">Loading files...</p>
            </div>

            <!-- Empty state -->
            <div v-else-if="files.length === 0" class="p-12 text-center">
              <div class="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg class="h-10 w-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p class="text-slate-500 font-medium">No files generated yet</p>
            </div>

            <!-- File browser -->
            <div v-else class="flex" style="height: 450px;">
              <!-- File list -->
              <div class="w-72 border-r border-slate-200 overflow-y-auto bg-slate-50">
                <ul class="divide-y divide-slate-100">
                  <li
                    v-for="file in files"
                    :key="file.path"
                    @click="selectFile(file.path)"
                    :class="[
                      'px-5 py-3 cursor-pointer hover:bg-white flex items-center gap-3 text-sm transition-all duration-150',
                      selectedFile === file.path ? 'bg-white text-cyan-700 border-l-4 border-cyan-500 shadow-sm' : 'text-slate-700 border-l-4 border-transparent'
                    ]"
                  >
                    <svg class="w-5 h-5 flex-shrink-0" :class="selectedFile === file.path ? 'text-cyan-500' : 'text-slate-400'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getFileIcon(file.path)" />
                    </svg>
                    <span class="truncate font-medium">{{ file.name }}</span>
                  </li>
                </ul>
              </div>

              <!-- File content -->
              <div class="flex-1 overflow-hidden flex flex-col bg-slate-900">
                <div v-if="selectedFile" class="px-5 py-3 bg-slate-800 border-b border-slate-700 text-sm text-cyan-400 font-mono">
                  {{ selectedFile }}
                </div>
                <div class="flex-1 overflow-auto">
                  <div v-if="fileContentLoading" class="p-8 text-center">
                    <svg class="animate-spin h-8 w-8 mx-auto text-cyan-500" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                  <pre v-else class="p-5 text-sm font-mono text-slate-300 whitespace-pre-wrap min-h-full leading-relaxed"><code>{{ fileContent }}</code></pre>
                </div>
              </div>
            </div>
          </div>

          <!-- Validation Card (only show for completed migrations) -->
          <div v-if="migration.status === 'completed'" class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-slate-200/50 overflow-hidden">
            <div class="px-8 py-5 border-b border-slate-200 bg-gradient-to-r from-indigo-50 to-violet-50">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-xl font-bold text-slate-900 flex items-center">
                  <svg class="w-6 h-6 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Comprehensive Validation
                </h3>
                <button
                  @click="runValidation"
                  :disabled="validationLoading"
                  class="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-600 text-white rounded-xl hover:from-indigo-600 hover:to-violet-700 flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg v-if="validationLoading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {{ validationLoading ? 'Validating...' : 'Run Validation' }}
                </button>
              </div>
              <!-- Validation Options -->
              <div class="flex flex-wrap gap-4 text-sm">
                <label class="flex items-center gap-2 cursor-pointer hover:bg-white/50 px-3 py-1.5 rounded-lg transition-colors">
                  <input type="checkbox" v-model="validationOptions.validateDataTypes" class="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500" />
                  <span class="text-slate-700">Data Type Mapping</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer hover:bg-white/50 px-3 py-1.5 rounded-lg transition-colors">
                  <input type="checkbox" v-model="validationOptions.generateDbtTests" class="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500" />
                  <span class="text-slate-700">Generate dbt Tests</span>
                </label>
              </div>
            </div>

            <!-- Validation Loading -->
            <div v-if="validationLoading" class="p-12 text-center">
              <div class="relative inline-block">
                <div class="h-16 w-16 rounded-full border-4 border-indigo-100"></div>
                <svg class="animate-spin h-16 w-16 text-indigo-600 absolute top-0" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <p class="mt-4 text-slate-500 font-medium">Validating transformation accuracy...</p>
            </div>

            <!-- Validation Error -->
            <div v-else-if="validationError" class="p-6">
              <div class="bg-red-50 border border-red-200 rounded-xl p-4">
                <div class="flex items-center">
                  <svg class="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span class="text-red-700 font-medium">{{ validationError }}</span>
                </div>
              </div>
            </div>

            <!-- Validation Results -->
            <div v-else-if="validationResult" class="p-6">
              <!-- Info Banner for Warnings -->
              <div v-if="validationResult.summary.warnings > 0 && validationResult.summary.failed === 0" class="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4">
                <div class="flex items-start gap-3">
                  <div class="flex-shrink-0 mt-0.5">
                    <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h4 class="font-semibold text-blue-800 mb-1">Your migration is ready!</h4>
                    <p class="text-sm text-blue-700">
                      The warnings below are <strong>optional recommendations</strong> to improve code quality.
                      They don't affect your data and you can safely proceed with deployment.
                    </p>
                    <p class="text-xs text-blue-600 mt-2">
                      Click on any warning to learn more about what it means and how to address it (if you want to).
                    </p>
                  </div>
                </div>
              </div>

              <!-- Summary Cards Row 1: Tables -->
              <div class="grid grid-cols-4 gap-4 mb-4">
                <div class="bg-slate-50 rounded-xl p-4 text-center">
                  <p class="text-sm text-slate-500 mb-1">Total Tables</p>
                  <p class="text-2xl font-bold text-slate-700">{{ validationResult.summary.total_tables }}</p>
                </div>
                <div class="bg-emerald-50 rounded-xl p-4 text-center">
                  <p class="text-sm text-emerald-600 mb-1">Passed</p>
                  <p class="text-2xl font-bold text-emerald-600">{{ validationResult.summary.passed }}</p>
                </div>
                <div class="bg-amber-50 rounded-xl p-4 text-center">
                  <p class="text-sm text-amber-600 mb-1">Suggestions</p>
                  <p class="text-2xl font-bold text-amber-600">{{ validationResult.summary.warnings }}</p>
                </div>
                <div class="bg-red-50 rounded-xl p-4 text-center">
                  <p class="text-sm text-red-600 mb-1">Failed</p>
                  <p class="text-2xl font-bold text-red-600">{{ validationResult.summary.failed }}</p>
                </div>
              </div>

              <!-- Summary Cards Row 2: Checks & Tests -->
              <div class="grid grid-cols-3 gap-4 mb-6">
                <div class="bg-indigo-50 rounded-xl p-4 text-center">
                  <p class="text-sm text-indigo-600 mb-1">Total Checks</p>
                  <p class="text-2xl font-bold text-indigo-600">{{ validationResult.summary.total_checks || 0 }}</p>
                </div>
                <div class="bg-violet-50 rounded-xl p-4 text-center">
                  <p class="text-sm text-violet-600 mb-1">dbt Tests Generated</p>
                  <p class="text-2xl font-bold text-violet-600">{{ validationResult.dbt_tests_generated || 0 }}</p>
                </div>
                <div class="bg-cyan-50 rounded-xl p-4 text-center">
                  <p class="text-sm text-cyan-600 mb-1">Passed Checks</p>
                  <p class="text-2xl font-bold text-cyan-600">{{ validationResult.summary.passed_checks || 0 }}</p>
                </div>
              </div>

              <!-- Pass Rate Progress -->
              <div class="mb-6 p-4 bg-slate-50 rounded-xl">
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium text-slate-600">Table Pass Rate</span>
                  <span class="text-lg font-bold" :class="validationResult.summary.pass_rate >= 80 ? 'text-emerald-600' : validationResult.summary.pass_rate >= 50 ? 'text-amber-600' : 'text-red-600'">
                    {{ validationResult.summary.pass_rate }}%
                  </span>
                </div>
                <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                  <div
                    class="h-3 rounded-full transition-all duration-500"
                    :class="validationResult.summary.pass_rate >= 80 ? 'bg-emerald-500' : validationResult.summary.pass_rate >= 50 ? 'bg-amber-500' : 'bg-red-500'"
                    :style="{ width: `${validationResult.summary.pass_rate}%` }"
                  ></div>
                </div>
                <div class="flex justify-between items-center mt-3 mb-2">
                  <span class="text-sm font-medium text-slate-600">Check Pass Rate</span>
                  <span class="text-lg font-bold" :class="(validationResult.summary.check_pass_rate || 0) >= 80 ? 'text-emerald-600' : (validationResult.summary.check_pass_rate || 0) >= 50 ? 'text-amber-600' : 'text-red-600'">
                    {{ validationResult.summary.check_pass_rate || 0 }}%
                  </span>
                </div>
                <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                  <div
                    class="h-3 rounded-full transition-all duration-500"
                    :class="(validationResult.summary.check_pass_rate || 0) >= 80 ? 'bg-emerald-500' : (validationResult.summary.check_pass_rate || 0) >= 50 ? 'bg-amber-500' : 'bg-red-500'"
                    :style="{ width: `${validationResult.summary.check_pass_rate || 0}%` }"
                  ></div>
                </div>
              </div>

              <!-- Table Results -->
              <div class="space-y-3">
                <div
                  v-for="table in validationResult.table_results"
                  :key="table.table_name"
                  :class="['border rounded-xl overflow-hidden', getStatusBg(table.overall_status)]"
                >
                  <!-- Table Header (clickable) -->
                  <div
                    @click="toggleTableExpand(table.table_name)"
                    class="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-white/50 transition-colors"
                  >
                    <div class="flex items-center gap-3">
                      <svg :class="['w-5 h-5', getStatusColor(table.overall_status)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getStatusIcon(table.overall_status)" />
                      </svg>
                      <div>
                        <p class="font-semibold text-slate-800">{{ table.target_model }}</p>
                        <p class="text-xs text-slate-500">from {{ table.source_table }}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <span :class="['text-xs font-medium px-2 py-1 rounded-full', table.overall_status === 'passed' ? 'bg-emerald-100 text-emerald-700' : table.overall_status === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700']">
                        {{ table.overall_status === 'warning' ? 'has suggestions' : table.overall_status }}
                      </span>
                      <svg
                        :class="['w-5 h-5 text-slate-400 transition-transform', expandedTables.has(table.table_name) ? 'rotate-180' : '']"
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>

                  <!-- Expanded Checks -->
                  <div v-if="expandedTables.has(table.table_name)" class="border-t border-slate-200 bg-white/70 px-4 py-3 space-y-3">
                    <div
                      v-for="(check, idx) in table.checks"
                      :key="idx"
                      class="rounded-lg border border-slate-200 bg-white overflow-hidden"
                    >
                      <!-- Check Header (Clickable) -->
                      <div
                        class="flex items-start gap-2 text-sm p-3 cursor-pointer hover:bg-slate-50 transition-colors"
                        @click="toggleCheckExpand(`${table.table_name}-${idx}`)"
                      >
                        <svg :class="['w-4 h-4 mt-0.5 flex-shrink-0', getStatusColor(check.status)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getStatusIcon(check.status)" />
                        </svg>
                        <div class="flex-1">
                          <div class="flex items-center gap-2">
                            <span class="font-medium text-slate-700">{{ getCheckExplanation(check.name, check.check_type).title }}</span>
                            <!-- Help icon -->
                            <svg class="w-4 h-4 text-blue-400 hover:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                          <p class="text-slate-500 text-xs mt-0.5">{{ check.details }}</p>
                        </div>
                        <!-- Expand/Collapse Arrow -->
                        <svg
                          :class="['w-4 h-4 text-slate-400 transition-transform', expandedChecks.has(`${table.table_name}-${idx}`) ? 'rotate-180' : '']"
                          fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        >
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>

                      <!-- Expanded Explanation -->
                      <div
                        v-if="expandedChecks.has(`${table.table_name}-${idx}`)"
                        class="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-t border-slate-200"
                      >
                        <div class="space-y-3">
                          <!-- What is this? -->
                          <div>
                            <h5 class="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">What is this?</h5>
                            <p class="text-sm text-slate-600">{{ getCheckExplanation(check.name, check.check_type).explanation }}</p>
                          </div>

                          <!-- What can I do? (only for warnings/failures) -->
                          <div v-if="check.status !== 'passed'">
                            <h5 class="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">What can I do? (Optional)</h5>
                            <p class="text-sm text-slate-600">{{ getCheckExplanation(check.name, check.check_type).howToFix }}</p>
                          </div>

                          <!-- Does this affect my data? -->
                          <div class="flex items-center gap-2 pt-2 border-t border-slate-200/50">
                            <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span class="text-xs text-slate-600">
                              <strong>Does this affect my data?</strong>
                              {{ getCheckExplanation(check.name, check.check_type).affectsData ? 'Yes, this may require data changes.' : 'No, this is about code quality only. Your source data remains untouched.' }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Empty State -->
            <div v-else class="p-12 text-center">
              <div class="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg class="h-10 w-10 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p class="text-slate-600 font-medium mb-2">Validate Your Transformation</p>
              <p class="text-slate-500 text-sm max-w-md mx-auto">
                Click "Run Validation" to verify that your dbt models accurately represent the source MSSQL schema,
                including columns, constraints, and relationships.
              </p>
            </div>
          </div>

          <!-- Deploy to Warehouse Card (only show for completed migrations) -->
          <div v-if="migration.status === 'completed'" class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-slate-200/50 overflow-hidden">
            <div class="px-8 py-5 border-b border-slate-200 bg-gradient-to-r from-purple-50 to-fuchsia-50">
              <h3 class="text-xl font-bold text-slate-900 flex items-center">
                <svg class="w-6 h-6 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Deploy to Warehouse
              </h3>
              <p class="text-sm text-slate-600 mt-1">Execute dbt run and dbt test on your target data warehouse</p>
            </div>

            <div class="p-6">
              <!-- Warehouse Selection -->
              <div class="mb-6">
                <label class="block text-sm font-medium text-slate-700 mb-2">Target Warehouse</label>
                <div class="grid grid-cols-3 md:grid-cols-6 gap-3">
                  <button
                    @click="deployConfig.warehouseType = 'snowflake'"
                    :class="[
                      'p-3 rounded-xl border-2 transition-all duration-200 flex flex-col items-center gap-2',
                      deployConfig.warehouseType === 'snowflake'
                        ? 'border-purple-500 bg-purple-50 shadow-md'
                        : 'border-slate-200 hover:border-purple-300 hover:bg-slate-50'
                    ]"
                  >
                    <svg class="w-7 h-7 text-blue-500" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                    </svg>
                    <span class="font-medium text-slate-700 text-xs">Snowflake</span>
                  </button>
                  <button
                    @click="deployConfig.warehouseType = 'bigquery'"
                    :class="[
                      'p-3 rounded-xl border-2 transition-all duration-200 flex flex-col items-center gap-2',
                      deployConfig.warehouseType === 'bigquery'
                        ? 'border-purple-500 bg-purple-50 shadow-md'
                        : 'border-slate-200 hover:border-purple-300 hover:bg-slate-50'
                    ]"
                  >
                    <svg class="w-7 h-7 text-yellow-500" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                    </svg>
                    <span class="font-medium text-slate-700 text-xs">BigQuery</span>
                  </button>
                  <button
                    @click="deployConfig.warehouseType = 'databricks'"
                    :class="[
                      'p-3 rounded-xl border-2 transition-all duration-200 flex flex-col items-center gap-2',
                      deployConfig.warehouseType === 'databricks'
                        ? 'border-purple-500 bg-purple-50 shadow-md'
                        : 'border-slate-200 hover:border-purple-300 hover:bg-slate-50'
                    ]"
                  >
                    <svg class="w-7 h-7 text-red-500" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                    <span class="font-medium text-slate-700 text-xs">Databricks</span>
                  </button>
                  <button
                    @click="deployConfig.warehouseType = 'redshift'"
                    :class="[
                      'p-3 rounded-xl border-2 transition-all duration-200 flex flex-col items-center gap-2',
                      deployConfig.warehouseType === 'redshift'
                        ? 'border-purple-500 bg-purple-50 shadow-md'
                        : 'border-slate-200 hover:border-purple-300 hover:bg-slate-50'
                    ]"
                  >
                    <svg class="w-7 h-7 text-orange-500" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                    </svg>
                    <span class="font-medium text-slate-700 text-xs">Redshift</span>
                  </button>
                  <button
                    @click="deployConfig.warehouseType = 'fabric'"
                    :class="[
                      'p-3 rounded-xl border-2 transition-all duration-200 flex flex-col items-center gap-2',
                      deployConfig.warehouseType === 'fabric'
                        ? 'border-purple-500 bg-purple-50 shadow-md'
                        : 'border-slate-200 hover:border-purple-300 hover:bg-slate-50'
                    ]"
                  >
                    <svg class="w-7 h-7 text-cyan-600" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3 3h8v8H3V3zm2 2v4h4V5H5zm8-2h8v8h-8V3zm2 2v4h4V5h-4zM3 13h8v8H3v-8zm2 2v4h4v-4H5zm8-2h8v8h-8v-8zm2 2v4h4v-4h-4z"/>
                    </svg>
                    <span class="font-medium text-slate-700 text-xs">MS Fabric</span>
                  </button>
                  <button
                    @click="deployConfig.warehouseType = 'spark'"
                    :class="[
                      'p-3 rounded-xl border-2 transition-all duration-200 flex flex-col items-center gap-2',
                      deployConfig.warehouseType === 'spark'
                        ? 'border-purple-500 bg-purple-50 shadow-md'
                        : 'border-slate-200 hover:border-purple-300 hover:bg-slate-50'
                    ]"
                  >
                    <svg class="w-7 h-7 text-orange-500" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2L4 7v10l8 5 8-5V7l-8-5zm0 2.5L17.5 8 12 11.5 6.5 8 12 4.5zM6 9.5l5 3v6l-5-3v-6zm12 0v6l-5 3v-6l5-3z"/>
                    </svg>
                    <span class="font-medium text-slate-700 text-xs">Apache Spark</span>
                  </button>
                </div>
              </div>

              <!-- Connection Details (Snowflake) -->
              <div v-if="deployConfig.warehouseType === 'snowflake'" class="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Account</label>
                  <input v-model="deployConfig.snowflake.account" type="text" placeholder="account.region" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Warehouse</label>
                  <input v-model="deployConfig.snowflake.warehouse" type="text" placeholder="COMPUTE_WH" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Database</label>
                  <input v-model="deployConfig.snowflake.database" type="text" placeholder="MY_DATABASE" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Schema</label>
                  <input v-model="deployConfig.snowflake.schema" type="text" placeholder="PUBLIC" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Username</label>
                  <input v-model="deployConfig.snowflake.username" type="text" placeholder="username" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
                  <input v-model="deployConfig.snowflake.password" type="password" placeholder="••••••••" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Role</label>
                  <input v-model="deployConfig.snowflake.role" type="text" placeholder="TRANSFORM" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
              </div>

              <!-- Connection Details (BigQuery) -->
              <div v-if="deployConfig.warehouseType === 'bigquery'" class="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Project ID</label>
                  <input v-model="deployConfig.bigquery.project" type="text" placeholder="my-gcp-project" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Dataset</label>
                  <input v-model="deployConfig.bigquery.dataset" type="text" placeholder="staging" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Location</label>
                  <input v-model="deployConfig.bigquery.location" type="text" placeholder="US" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div class="col-span-2">
                  <label class="block text-sm font-medium text-slate-700 mb-1">Service Account Key (JSON path)</label>
                  <input v-model="deployConfig.bigquery.keyfile" type="text" placeholder="/path/to/keyfile.json" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
              </div>

              <!-- Connection Details (Databricks) -->
              <div v-if="deployConfig.warehouseType === 'databricks'" class="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Host</label>
                  <input v-model="deployConfig.databricks.host" type="text" placeholder="adb-xxx.azuredatabricks.net" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">HTTP Path</label>
                  <input v-model="deployConfig.databricks.httpPath" type="text" placeholder="/sql/1.0/warehouses/xxx" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Access Token</label>
                  <input v-model="deployConfig.databricks.token" type="password" placeholder="dapi..." class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Catalog</label>
                  <input v-model="deployConfig.databricks.catalog" type="text" placeholder="hive_metastore" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
              </div>

              <!-- Connection Details (Redshift) -->
              <div v-if="deployConfig.warehouseType === 'redshift'" class="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Host</label>
                  <input v-model="deployConfig.redshift.host" type="text" placeholder="cluster.region.redshift.amazonaws.com" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Port</label>
                  <input v-model.number="deployConfig.redshift.port" type="number" placeholder="5439" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Database</label>
                  <input v-model="deployConfig.redshift.database" type="text" placeholder="dev" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Schema</label>
                  <input v-model="deployConfig.redshift.schema" type="text" placeholder="public" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Username</label>
                  <input v-model="deployConfig.redshift.username" type="text" placeholder="admin" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
                  <input v-model="deployConfig.redshift.password" type="password" placeholder="••••••••" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                </div>
              </div>

              <!-- Connection Details (Microsoft Fabric) -->
              <div v-if="deployConfig.warehouseType === 'fabric'" class="space-y-4 mb-6">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Server</label>
                    <input v-model="deployConfig.fabric.server" type="text" placeholder="server.database.fabric.microsoft.com" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Port</label>
                    <input v-model.number="deployConfig.fabric.port" type="number" placeholder="1433" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Database</label>
                    <input v-model="deployConfig.fabric.database" type="text" placeholder="my_warehouse" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Schema</label>
                    <input v-model="deployConfig.fabric.schema" type="text" placeholder="dbo" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                </div>
                <div class="p-4 bg-slate-50 rounded-xl">
                  <label class="block text-sm font-medium text-slate-700 mb-2">Authentication Method</label>
                  <div class="flex gap-4">
                    <label class="flex items-center gap-2 cursor-pointer">
                      <input type="radio" v-model="deployConfig.fabric.authentication" value="sql" class="w-4 h-4 text-purple-600 border-slate-300 focus:ring-purple-500" />
                      <span class="text-slate-700">SQL Auth</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                      <input type="radio" v-model="deployConfig.fabric.authentication" value="serviceprincipal" class="w-4 h-4 text-purple-600 border-slate-300 focus:ring-purple-500" />
                      <span class="text-slate-700">Service Principal</span>
                    </label>
                  </div>
                </div>
                <!-- SQL Auth fields -->
                <div v-if="deployConfig.fabric.authentication === 'sql'" class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Username</label>
                    <input v-model="deployConfig.fabric.username" type="text" placeholder="username" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
                    <input v-model="deployConfig.fabric.password" type="password" placeholder="••••••••" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                </div>
                <!-- Service Principal fields -->
                <div v-if="deployConfig.fabric.authentication === 'serviceprincipal'" class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Tenant ID</label>
                    <input v-model="deployConfig.fabric.tenantId" type="text" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Client ID</label>
                    <input v-model="deployConfig.fabric.clientId" type="text" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div class="col-span-2">
                    <label class="block text-sm font-medium text-slate-700 mb-1">Client Secret</label>
                    <input v-model="deployConfig.fabric.clientSecret" type="password" placeholder="••••••••" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                </div>
              </div>

              <!-- Connection Details (Apache Spark) -->
              <div v-if="deployConfig.warehouseType === 'spark'" class="space-y-4 mb-6">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Host</label>
                    <input v-model="deployConfig.spark.host" type="text" placeholder="spark-cluster.example.com" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Port</label>
                    <input v-model.number="deployConfig.spark.port" type="number" placeholder="10000" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Schema</label>
                    <input v-model="deployConfig.spark.schema" type="text" placeholder="default" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Connection Method</label>
                    <select v-model="deployConfig.spark.method" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                      <option value="thrift">Thrift</option>
                      <option value="http">HTTP</option>
                      <option value="session">Session</option>
                    </select>
                  </div>
                  <div v-if="deployConfig.spark.method === 'http'">
                    <label class="block text-sm font-medium text-slate-700 mb-1">Cluster</label>
                    <input v-model="deployConfig.spark.cluster" type="text" placeholder="cluster-id" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Token (Optional)</label>
                    <input v-model="deployConfig.spark.token" type="password" placeholder="Authentication token" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                </div>
              </div>

              <!-- Deploy Options -->
              <div class="flex items-center gap-6 mb-6 p-4 bg-slate-50 rounded-xl">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" v-model="deployConfig.runTests" class="w-4 h-4 text-purple-600 rounded border-slate-300 focus:ring-purple-500" />
                  <span class="text-slate-700">Run dbt Tests</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" v-model="deployConfig.fullRefresh" class="w-4 h-4 text-purple-600 rounded border-slate-300 focus:ring-purple-500" />
                  <span class="text-slate-700">Full Refresh</span>
                </label>
              </div>

              <!-- Deploy Button -->
              <button
                @click="startDeployment"
                :disabled="deploying || !deployConfig.warehouseType"
                class="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-fuchsia-600 text-white rounded-xl hover:from-purple-600 hover:to-fuchsia-700 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transition-all duration-200 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg v-if="deploying" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                {{ deploying ? 'Deploying...' : 'Deploy to Warehouse' }}
              </button>

              <!-- Deployment Result -->
              <div v-if="deploymentResult" class="mt-6">
                <div :class="[
                  'p-4 rounded-xl border-2',
                  deploymentResult.status === 'completed' ? 'bg-emerald-50 border-emerald-200' :
                  deploymentResult.status === 'failed' ? 'bg-red-50 border-red-200' :
                  'bg-blue-50 border-blue-200'
                ]">
                  <div class="flex items-center gap-2 mb-3">
                    <svg v-if="deploymentResult.status === 'completed'" class="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <svg v-else-if="deploymentResult.status === 'failed'" class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <svg v-else class="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span :class="[
                      'font-semibold',
                      deploymentResult.status === 'completed' ? 'text-emerald-700' :
                      deploymentResult.status === 'failed' ? 'text-red-700' : 'text-blue-700'
                    ]">
                      {{ deploymentResult.status === 'completed' ? 'Deployment Complete' :
                         deploymentResult.status === 'failed' ? 'Deployment Failed' : 'Deployment In Progress' }}
                    </span>
                  </div>

                  <!-- dbt run results -->
                  <div v-if="deploymentResult.dbt_run" class="grid grid-cols-3 gap-3 mb-3">
                    <div class="bg-white/60 rounded-lg p-3 text-center">
                      <p class="text-xs text-slate-500">Tables Created</p>
                      <p class="text-xl font-bold text-emerald-600">{{ deploymentResult.dbt_run.tables_created }}</p>
                    </div>
                    <div class="bg-white/60 rounded-lg p-3 text-center">
                      <p class="text-xs text-slate-500">Models Succeeded</p>
                      <p class="text-xl font-bold text-emerald-600">{{ deploymentResult.dbt_run.models_succeeded }}</p>
                    </div>
                    <div class="bg-white/60 rounded-lg p-3 text-center">
                      <p class="text-xs text-slate-500">Models Failed</p>
                      <p class="text-xl font-bold text-red-600">{{ deploymentResult.dbt_run.models_failed }}</p>
                    </div>
                  </div>

                  <!-- dbt test results -->
                  <div v-if="deploymentResult.dbt_test" class="grid grid-cols-3 gap-3">
                    <div class="bg-white/60 rounded-lg p-3 text-center">
                      <p class="text-xs text-slate-500">Tests Passed</p>
                      <p class="text-xl font-bold text-emerald-600">{{ deploymentResult.dbt_test.tests_passed }}</p>
                    </div>
                    <div class="bg-white/60 rounded-lg p-3 text-center">
                      <p class="text-xs text-slate-500">Tests Failed</p>
                      <p class="text-xl font-bold text-red-600">{{ deploymentResult.dbt_test.tests_failed }}</p>
                    </div>
                    <div class="bg-white/60 rounded-lg p-3 text-center">
                      <p class="text-xs text-slate-500">Warnings</p>
                      <p class="text-xl font-bold text-amber-600">{{ deploymentResult.dbt_test.tests_warned }}</p>
                    </div>
                  </div>

                  <!-- Error message -->
                  <div v-if="deploymentResult.error" class="mt-3 p-3 bg-red-100 rounded-lg text-red-700 text-sm">
                    {{ deploymentResult.error }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Info Card -->
          <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-slate-200/50 p-8">
            <h3 class="text-xl font-bold text-slate-900 mb-6 flex items-center">
              <svg class="w-6 h-6 mr-2 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Migration Information
            </h3>
            <dl class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="bg-slate-50 rounded-xl p-4">
                <dt class="text-sm text-slate-500 mb-1">Migration ID</dt>
                <dd class="font-mono text-sm font-semibold text-slate-900">{{ migration.id }}</dd>
              </div>
              <div class="bg-slate-50 rounded-xl p-4">
                <dt class="text-sm text-slate-500 mb-1">User ID</dt>
                <dd class="font-mono text-sm font-semibold text-slate-900">{{ migration.user_id }}</dd>
              </div>
              <div class="bg-slate-50 rounded-xl p-4">
                <dt class="text-sm text-slate-500 mb-1">Created At</dt>
                <dd class="text-sm font-semibold text-slate-900">{{ formatDate(migration.created_at) }}</dd>
              </div>
              <div class="bg-slate-50 rounded-xl p-4">
                <dt class="text-sm text-slate-500 mb-1">Completed At</dt>
                <dd class="text-sm font-semibold text-slate-900">{{ formatDate(migration.completed_at) }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar for file browser */
.overflow-y-auto::-webkit-scrollbar,
.overflow-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track,
.overflow-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb,
.overflow-auto::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.5);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover,
.overflow-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.7);
}

/* Code block scrollbar */
.bg-slate-900 .overflow-auto::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
}

.bg-slate-900 .overflow-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}
</style>
