<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { aiService } from '../services/api'

const { t } = useI18n()

// Live health data from API
const liveHealthData = ref<Record<string, { status: string; importable: boolean; error?: string }>>({})
const healthCheckLoading = ref(false)
const healthCheckError = ref<string | null>(null)

// Supervisor metrics
const supervisorMetrics = ref<{
  total_requests: number
  routing_decisions: Record<string, number>
  average_confidence: number
} | null>(null)

type ProductionStatus = 'production' | 'beta' | 'coming-soon'

interface Agent {
  id: string
  name: string
  description: string
  longDescription: string
  badge: string
  color: string
  icon: string
  status: 'active' | 'idle' | 'processing' | 'error'
  productionStatus: ProductionStatus
  completionPercent: number
  lastRun: string | null
  processedItems: number
  capabilities: string[]
  techStack: string[]
}

const agents = ref<Agent[]>([
  {
    id: 'mssql-extractor',
    name: 'MSSQL Extractor',
    description: 'Intelligently extracts schemas, relationships, and metadata from your MSSQL databases',
    longDescription: 'The MSSQL Extractor Agent connects to your SQL Server databases and performs deep analysis of your schema structure. It identifies tables, columns, data types, primary keys, foreign keys, indexes, views, stored procedures, and triggers. The agent also detects relationships between tables and generates a comprehensive metadata model.',
    badge: 'Schema Analysis',
    color: 'blue',
    icon: 'database',
    status: 'active',
    productionStatus: 'production',
    completionPercent: 95,
    lastRun: '2024-12-05T10:30:00',
    processedItems: 1250,
    capabilities: ['Schema extraction', 'Relationship detection', 'Index analysis', 'View & SP mapping', 'Data type inference'],
    techStack: ['pyodbc', 'SQLAlchemy', 'pandas']
  },
  {
    id: 'dbt-generator',
    name: 'dbt Generator',
    description: 'Automatically creates production-ready dbt models, tests, and documentation',
    longDescription: 'The dbt Generator Agent takes your extracted schema and generates a complete dbt project. It creates staging models, intermediate transformations, and mart models following dbt best practices. The agent also generates tests, documentation, and source definitions.',
    badge: 'Code Generation',
    color: 'orange',
    icon: 'code',
    status: 'active',
    productionStatus: 'production',
    completionPercent: 95,
    lastRun: '2024-12-05T08:45:00',
    processedItems: 89,
    capabilities: ['Model generation', 'Test creation', 'Documentation', 'Source definitions', 'Materialization config'],
    techStack: ['Jinja2', 'dbt-core', 'YAML']
  },
  {
    id: 'dbt-executor',
    name: 'dbt Executor',
    description: 'Runs dbt commands, manages dependencies, and handles incremental builds',
    longDescription: 'The dbt Executor Agent manages the execution of dbt commands in your target environment. It handles full refreshes, incremental builds, test runs, and documentation generation. The agent monitors execution progress and reports any failures.',
    badge: 'Execution',
    color: 'teal',
    icon: 'play',
    status: 'idle',
    productionStatus: 'beta',
    completionPercent: 70,
    lastRun: '2024-12-05T08:50:00',
    processedItems: 156,
    capabilities: ['dbt run', 'dbt test', 'dbt docs', 'Incremental builds', 'Dependency management'],
    techStack: ['dbt-core', 'dbt-snowflake', 'dbt-bigquery']
  },
  {
    id: 'data-quality',
    name: 'Data Quality Agent',
    description: 'Validates data integrity with 50+ quality checks and anomaly detection',
    longDescription: 'The Data Quality Agent performs comprehensive validation of your data. It runs over 50 quality checks including null checks, uniqueness validation, referential integrity, and business rule validation. The agent uses ML to detect anomalies and data drift.',
    badge: 'Validation',
    color: 'green',
    icon: 'shield-check',
    status: 'idle',
    productionStatus: 'beta',
    completionPercent: 60,
    lastRun: '2024-12-05T07:30:00',
    processedItems: 45000,
    capabilities: ['Null checking', 'Uniqueness validation', 'Referential integrity', 'Anomaly detection', 'Data drift monitoring'],
    techStack: ['Great Expectations', 'pandas', 'scipy']
  },
  {
    id: 'validation',
    name: 'Validation Agent',
    description: 'Self-healing validation with Actor-Critic pattern for automatic error recovery',
    longDescription: 'The Validation Agent implements the Actor-Critic self-healing pattern from "Building Applications with AI Agents" (O\'Reilly, 2025). It validates migrations against a quality rubric (schema completeness, data type accuracy, referential integrity, dbt syntax, test coverage, documentation). When issues are detected, it automatically regenerates and re-validates up to 3 times.',
    badge: 'Actor-Critic',
    color: 'amber',
    icon: 'clipboard-check',
    status: 'active',
    productionStatus: 'beta',
    completionPercent: 65,
    lastRun: new Date().toISOString(),
    processedItems: 89000,
    capabilities: ['Actor-Critic self-healing', 'Quality rubric scoring', 'Automatic regeneration', 'Row count validation', 'dbt syntax validation', 'Test coverage analysis'],
    techStack: ['LangGraph', 'pandas', 'pyodbc']
  },
  {
    id: 'rag-service',
    name: 'RAG Service',
    description: 'Retrieval-augmented generation for intelligent query assistance',
    longDescription: 'The RAG Service Agent provides intelligent query assistance using retrieval-augmented generation. It indexes your schema documentation and can answer questions about your data models, suggest SQL queries, and provide contextual help.',
    badge: 'AI Learning',
    color: 'pink',
    icon: 'light-bulb',
    status: 'idle',
    productionStatus: 'beta',
    completionPercent: 85,
    lastRun: null,
    processedItems: 12500,
    capabilities: ['Query assistance', 'Schema Q&A', 'SQL suggestions', 'Context-aware help', 'Learning from feedback'],
    techStack: ['LangChain', 'ChromaDB', 'OpenAI']
  },
  {
    id: 'dataprep',
    name: 'DataPrep Agent',
    description: 'Cleans, transforms, and prepares your data for the target warehouse',
    longDescription: 'The DataPrep Agent handles all data preparation tasks including profiling, cleaning, deduplication, and transformation. It uses ML algorithms to detect anomalies, missing values, and outliers. The agent can automatically suggest and apply data quality fixes.',
    badge: 'Transformation',
    color: 'purple',
    icon: 'beaker',
    status: 'idle',
    productionStatus: 'coming-soon',
    completionPercent: 25,
    lastRun: null,
    processedItems: 0,
    capabilities: ['Data profiling', 'Deduplication', 'Outlier detection', 'Missing value handling', 'Type conversion'],
    techStack: ['pandas', 'numpy', 'scikit-learn']
  },
  {
    id: 'documentation',
    name: 'Documentation Agent',
    description: 'Auto-generates comprehensive documentation and data lineage maps',
    longDescription: 'The Documentation Agent creates rich documentation for your data models. It generates column descriptions, table overviews, data lineage diagrams, and ERD visualizations. The agent can also create data dictionaries and business glossaries.',
    badge: 'Auto-Docs',
    color: 'cyan',
    icon: 'document-text',
    status: 'idle',
    productionStatus: 'coming-soon',
    completionPercent: 20,
    lastRun: null,
    processedItems: 0,
    capabilities: ['Auto descriptions', 'Lineage mapping', 'ERD generation', 'Data dictionary', 'Business glossary'],
    techStack: ['OpenAI', 'Mermaid.js', 'Markdown']
  },
  {
    id: 'bi-analytics',
    name: 'BI Analytics',
    description: 'Generates insights, dashboards, and business intelligence reports',
    longDescription: 'The BI Analytics Agent analyzes your data and generates insights automatically. It can create summary statistics, trend analysis, and suggest visualizations. The agent integrates with popular BI tools like Metabase, Looker, and Tableau.',
    badge: 'Insights',
    color: 'indigo',
    icon: 'chart-bar',
    status: 'idle',
    productionStatus: 'coming-soon',
    completionPercent: 15,
    lastRun: null,
    processedItems: 0,
    capabilities: ['Auto insights', 'Trend detection', 'Visualization suggestions', 'BI tool integration', 'Report generation'],
    techStack: ['pandas', 'plotly', 'Metabase API']
  },
  {
    id: 'ml-finetuning',
    name: 'ML Fine-Tuning',
    description: 'Trains and optimizes custom AI models for your specific data patterns',
    longDescription: 'The ML Fine-Tuning Agent trains custom models on your data to improve accuracy. It can fine-tune embeddings for better RAG performance, train classification models for data quality, and optimize transformation suggestions.',
    badge: 'AI Training',
    color: 'rose',
    icon: 'academic-cap',
    status: 'idle',
    productionStatus: 'coming-soon',
    completionPercent: 10,
    lastRun: null,
    processedItems: 0,
    capabilities: ['Embedding fine-tuning', 'Classification training', 'Model optimization', 'Transfer learning', 'AutoML'],
    techStack: ['PyTorch', 'HuggingFace', 'scikit-learn']
  },
  {
    id: 'guardian',
    name: 'Guardian Agent',
    description: 'Orchestrates all agents, monitors pipeline health, and ensures safe operations with MAESTRO security framework',
    longDescription: 'The Guardian Agent is the orchestrator that manages all other agents. It implements the MAESTRO 7-layer security framework from "Building Applications with AI Agents" (O\'Reilly, 2025). Features include input sanitization, output filtering, rate limiting, prompt injection prevention, and comprehensive audit logging.',
    badge: 'Security',
    color: 'violet',
    icon: 'shield-exclamation',
    status: 'active',
    productionStatus: 'beta',
    completionPercent: 40,
    lastRun: new Date().toISOString(),
    processedItems: 0,
    capabilities: ['MAESTRO 7-layer security', 'Input sanitization', 'Prompt injection prevention', 'Rate limiting', 'Audit logging', 'Security assessment'],
    techStack: ['LangGraph', 'Pydantic', 'FastAPI']
  }
])

const selectedAgent = ref<Agent | null>(null)
const searchQuery = ref('')
const filterStatus = ref<string>('all')

const filteredAgents = computed(() => {
  return agents.value.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         agent.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesFilter = filterStatus.value === 'all' || agent.status === filterStatus.value
    return matchesSearch && matchesFilter
  })
})

const activeAgentsCount = computed(() => agents.value.filter(a => a.status === 'active').length)
const processingAgentsCount = computed(() => agents.value.filter(a => a.status === 'processing').length)
const totalProcessedItems = computed(() => agents.value.reduce((sum, a) => sum + a.processedItems, 0))

const getColorClasses = (color: string) => {
  const colors: Record<string, { bg: string; border: string; text: string; light: string; gradient: string }> = {
    blue: { bg: 'bg-blue-500', border: 'border-blue-500/30', text: 'text-blue-400', light: 'bg-blue-500/10', gradient: 'from-blue-500 to-blue-600' },
    purple: { bg: 'bg-purple-500', border: 'border-purple-500/30', text: 'text-purple-400', light: 'bg-purple-500/10', gradient: 'from-purple-500 to-purple-600' },
    orange: { bg: 'bg-orange-500', border: 'border-orange-500/30', text: 'text-orange-400', light: 'bg-orange-500/10', gradient: 'from-orange-500 to-orange-600' },
    teal: { bg: 'bg-teal-500', border: 'border-teal-500/30', text: 'text-teal-400', light: 'bg-teal-500/10', gradient: 'from-teal-500 to-teal-600' },
    green: { bg: 'bg-green-500', border: 'border-green-500/30', text: 'text-green-400', light: 'bg-green-500/10', gradient: 'from-green-500 to-green-600' },
    cyan: { bg: 'bg-cyan-500', border: 'border-cyan-500/30', text: 'text-cyan-400', light: 'bg-cyan-500/10', gradient: 'from-cyan-500 to-cyan-600' },
    pink: { bg: 'bg-pink-500', border: 'border-pink-500/30', text: 'text-pink-400', light: 'bg-pink-500/10', gradient: 'from-pink-500 to-pink-600' },
    indigo: { bg: 'bg-indigo-500', border: 'border-indigo-500/30', text: 'text-indigo-400', light: 'bg-indigo-500/10', gradient: 'from-indigo-500 to-indigo-600' },
    amber: { bg: 'bg-amber-500', border: 'border-amber-500/30', text: 'text-amber-400', light: 'bg-amber-500/10', gradient: 'from-amber-500 to-amber-600' },
    rose: { bg: 'bg-rose-500', border: 'border-rose-500/30', text: 'text-rose-400', light: 'bg-rose-500/10', gradient: 'from-rose-500 to-rose-600' },
    violet: { bg: 'bg-violet-500', border: 'border-violet-500/30', text: 'text-violet-400', light: 'bg-violet-500/10', gradient: 'from-violet-500 to-violet-600' }
  }
  return colors[color] || colors.blue
}

const getStatusClasses = (status: string) => {
  switch (status) {
    case 'active': return { bg: 'bg-emerald-500', text: 'text-emerald-400', label: 'Active', pulse: true }
    case 'processing': return { bg: 'bg-blue-500', text: 'text-blue-400', label: 'Processing', pulse: true }
    case 'error': return { bg: 'bg-red-500', text: 'text-red-400', label: 'Error', pulse: false }
    default: return { bg: 'bg-slate-500', text: 'text-slate-400', label: 'Idle', pulse: false }
  }
}

const getProductionStatusClasses = (status: ProductionStatus) => {
  switch (status) {
    case 'production': return {
      bg: 'bg-emerald-100',
      text: 'text-emerald-700',
      border: 'border-emerald-200',
      label: 'Production',
      icon: 'check-circle'
    }
    case 'beta': return {
      bg: 'bg-amber-100',
      text: 'text-amber-700',
      border: 'border-amber-200',
      label: 'Beta',
      icon: 'beaker'
    }
    case 'coming-soon': return {
      bg: 'bg-slate-100',
      text: 'text-slate-600',
      border: 'border-slate-200',
      label: 'Coming Soon',
      icon: 'clock'
    }
  }
}

const productionAgentsCount = computed(() => agents.value.filter(a => a.productionStatus === 'production').length)
const betaAgentsCount = computed(() => agents.value.filter(a => a.productionStatus === 'beta').length)
const comingSoonAgentsCount = computed(() => agents.value.filter(a => a.productionStatus === 'coming-soon').length)

const formatDate = (dateString: string | null) => {
  if (!dateString) return 'Running now'
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (hours < 1) return 'Just now'
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const openAgentDetail = (agent: Agent) => {
  selectedAgent.value = agent
}

const closeDetail = () => {
  selectedAgent.value = null
}

// Fetch live health data from API
const fetchHealthData = async () => {
  healthCheckLoading.value = true
  healthCheckError.value = null
  try {
    const response = await aiService.getAgentsHealth()
    // Map API response to our health data format
    if (response.agents) {
      const healthMap: Record<string, { status: string; importable: boolean; error?: string }> = {}
      for (const [id, data] of Object.entries(response.agents)) {
        healthMap[id] = {
          status: data.health?.status || 'unknown',
          importable: data.health?.importable || false,
          error: data.health?.error
        }
      }
      liveHealthData.value = healthMap
    }
  } catch (error: any) {
    healthCheckError.value = error.message || 'Failed to fetch health data'
    console.error('Failed to fetch agent health:', error)
  } finally {
    healthCheckLoading.value = false
  }
}

// Fetch supervisor metrics
const fetchSupervisorMetrics = async () => {
  try {
    const response = await aiService.getSupervisorMetrics()
    supervisorMetrics.value = {
      total_requests: response.total_requests,
      routing_decisions: response.routing_decisions,
      average_confidence: response.average_confidence
    }
  } catch (error) {
    console.error('Failed to fetch supervisor metrics:', error)
  }
}

// Get live status for an agent
const getLiveStatus = (agentId: string): 'healthy' | 'unhealthy' | 'degraded' | 'unknown' => {
  const idMap: Record<string, string> = {
    'mssql-extractor': 'mssql_extractor',
    'dbt-generator': 'dbt_generator',
    'dbt-executor': 'dbt_executor',
    'data-quality': 'data_quality_agent',
    'validation': 'validation_agent',
    'rag-service': 'rag_service',
    'guardian': 'guardian_agent',
    'dataprep': 'dataprep_agent',
    'documentation': 'documentation_agent',
    'bi-analytics': 'bi_agent',
    'ml-finetuning': 'ml_finetuning_agent'
  }
  const apiId = idMap[agentId]
  if (apiId && liveHealthData.value[apiId]) {
    return liveHealthData.value[apiId].status as any
  }
  return 'unknown'
}

// Simulate agent status updates and fetch live data
let statusInterval: number | null = null
let healthInterval: number | null = null
onMounted(() => {
  // Fetch initial health data
  fetchHealthData()
  fetchSupervisorMetrics()

  // Update processed items simulation
  statusInterval = window.setInterval(() => {
    agents.value.forEach(agent => {
      if (agent.status === 'active' || agent.status === 'processing') {
        agent.processedItems += Math.floor(Math.random() * 10)
      }
    })
  }, 3000)

  // Refresh health data every 30 seconds
  healthInterval = window.setInterval(() => {
    fetchHealthData()
    fetchSupervisorMetrics()
  }, 30000)
})

onUnmounted(() => {
  if (statusInterval) clearInterval(statusInterval)
  if (healthInterval) clearInterval(healthInterval)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/30">
    <!-- Header -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-8">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div class="flex items-center">
              <div class="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-xl p-3 mr-4 shadow-lg shadow-cyan-500/25">
                <svg class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                </svg>
              </div>
              <div>
                <h1 class="text-3xl font-bold text-white">AI Agents</h1>
                <p class="mt-1 text-slate-300">11 specialized agents powering your migrations</p>
              </div>
            </div>

            <!-- Stats -->
            <div class="mt-6 lg:mt-0 flex items-center space-x-3">
              <div class="bg-emerald-500/20 backdrop-blur-sm rounded-xl px-4 py-2 border border-emerald-500/30">
                <div class="flex items-center space-x-2">
                  <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <span class="text-white font-semibold">{{ productionAgentsCount }}</span>
                  <span class="text-emerald-300 text-sm">Production</span>
                </div>
              </div>
              <div class="bg-amber-500/20 backdrop-blur-sm rounded-xl px-4 py-2 border border-amber-500/30">
                <div class="flex items-center space-x-2">
                  <svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
                  </svg>
                  <span class="text-white font-semibold">{{ betaAgentsCount }}</span>
                  <span class="text-amber-300 text-sm">Beta</span>
                </div>
              </div>
              <div class="bg-slate-500/20 backdrop-blur-sm rounded-xl px-4 py-2 border border-slate-500/30">
                <div class="flex items-center space-x-2">
                  <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <span class="text-white font-semibold">{{ comingSoonAgentsCount }}</span>
                  <span class="text-slate-300 text-sm">Coming Soon</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <!-- Search and Filter -->
      <div class="mb-8 flex flex-col sm:flex-row gap-4">
        <div class="flex-1 relative">
          <svg class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search agents..."
            class="w-full pl-12 pr-4 py-3 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all"
          />
        </div>
        <div class="flex gap-2">
          <button
            @click="filterStatus = 'all'"
            :class="[
              'px-4 py-2 rounded-xl text-sm font-medium transition-all',
              filterStatus === 'all' ? 'bg-slate-900 text-white' : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
            ]"
          >
            All
          </button>
          <button
            @click="filterStatus = 'active'"
            :class="[
              'px-4 py-2 rounded-xl text-sm font-medium transition-all',
              filterStatus === 'active' ? 'bg-emerald-500 text-white' : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
            ]"
          >
            Active
          </button>
          <button
            @click="filterStatus = 'idle'"
            :class="[
              'px-4 py-2 rounded-xl text-sm font-medium transition-all',
              filterStatus === 'idle' ? 'bg-slate-500 text-white' : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
            ]"
          >
            Idle
          </button>
        </div>
      </div>

      <!-- Agents Grid -->
      <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="agent in filteredAgents"
          :key="agent.id"
          @click="openAgentDetail(agent)"
          class="group bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer hover:-translate-y-1 overflow-hidden"
        >
          <!-- Card Header -->
          <div :class="['p-6 border-b border-gray-100', `bg-gradient-to-r ${getColorClasses(agent.color).light}`]">
            <div class="flex items-start justify-between">
              <div class="flex items-center space-x-4">
                <div :class="[
                  'w-14 h-14 rounded-xl flex items-center justify-center shadow-lg',
                  `bg-gradient-to-br ${getColorClasses(agent.color).gradient}`
                ]">
                  <!-- Dynamic Icons -->
                  <svg v-if="agent.icon === 'database'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                  </svg>
                  <svg v-else-if="agent.icon === 'beaker'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
                  </svg>
                  <svg v-else-if="agent.icon === 'code'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
                  </svg>
                  <svg v-else-if="agent.icon === 'play'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <svg v-else-if="agent.icon === 'shield-check'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                  </svg>
                  <svg v-else-if="agent.icon === 'document-text'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                  </svg>
                  <svg v-else-if="agent.icon === 'light-bulb'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                  </svg>
                  <svg v-else-if="agent.icon === 'chart-bar'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                  </svg>
                  <svg v-else-if="agent.icon === 'clipboard-check'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
                  </svg>
                  <svg v-else-if="agent.icon === 'academic-cap'" class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222"/>
                  </svg>
                  <svg v-else class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-slate-800 group-hover:text-cyan-600 transition-colors">{{ agent.name }}</h3>
                  <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', getColorClasses(agent.color).light, getColorClasses(agent.color).text]">
                    {{ agent.badge }}
                  </span>
                </div>
              </div>

              <!-- Production Status Badge -->
              <div :class="[
                'flex items-center space-x-1 px-2 py-1 rounded-lg text-xs font-medium border',
                getProductionStatusClasses(agent.productionStatus).bg,
                getProductionStatusClasses(agent.productionStatus).text,
                getProductionStatusClasses(agent.productionStatus).border
              ]">
                <svg v-if="agent.productionStatus === 'production'" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <svg v-else-if="agent.productionStatus === 'beta'" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
                </svg>
                <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span>{{ getProductionStatusClasses(agent.productionStatus).label }}</span>
              </div>
            </div>
          </div>

          <!-- Card Body -->
          <div class="p-6">
            <p class="text-slate-600 text-sm mb-4">{{ agent.description }}</p>

            <!-- Completion Progress -->
            <div class="mb-4">
              <div class="flex items-center justify-between text-xs mb-1">
                <span class="text-slate-500">Completion</span>
                <span :class="[
                  'font-semibold',
                  agent.completionPercent >= 90 ? 'text-emerald-600' :
                  agent.completionPercent >= 50 ? 'text-amber-600' : 'text-slate-500'
                ]">{{ agent.completionPercent }}%</span>
              </div>
              <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  :class="[
                    'h-full rounded-full transition-all',
                    agent.completionPercent >= 90 ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' :
                    agent.completionPercent >= 50 ? 'bg-gradient-to-r from-amber-500 to-amber-400' :
                    'bg-gradient-to-r from-slate-400 to-slate-300'
                  ]"
                  :style="{ width: `${agent.completionPercent}%` }"
                ></div>
              </div>
            </div>

            <div class="flex items-center justify-between text-sm">
              <div v-if="agent.lastRun" class="flex items-center space-x-1 text-slate-500">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span>{{ formatDate(agent.lastRun) }}</span>
              </div>
              <div v-else class="flex items-center space-x-1 text-slate-400">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span>Not yet run</span>
              </div>
              <div v-if="agent.processedItems > 0" class="flex items-center space-x-1 text-slate-500">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
                <span>{{ formatNumber(agent.processedItems) }} items</span>
              </div>
            </div>
          </div>

          <!-- Card Footer -->
          <div class="px-6 py-3 bg-slate-50 border-t border-gray-100 flex justify-end">
            <span class="text-sm text-cyan-600 font-medium group-hover:translate-x-1 transition-transform inline-flex items-center">
              View Details
              <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Agent Detail Modal -->
    <Teleport to="body">
      <div v-if="selectedAgent" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex items-start justify-center min-h-screen pt-16 px-4">
          <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" @click="closeDetail"></div>
          <div class="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full overflow-hidden border border-gray-200">
            <!-- Modal Header -->
            <div :class="['p-6 border-b border-gray-100', `bg-gradient-to-r ${getColorClasses(selectedAgent.color).light}`]">
              <div class="flex items-start justify-between">
                <div class="flex items-center space-x-4">
                  <div :class="[
                    'w-16 h-16 rounded-xl flex items-center justify-center shadow-lg',
                    `bg-gradient-to-br ${getColorClasses(selectedAgent.color).gradient}`
                  ]">
                    <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                    </svg>
                  </div>
                  <div>
                    <h2 class="text-2xl font-bold text-slate-800">{{ selectedAgent.name }}</h2>
                    <div class="flex items-center space-x-2 mt-1">
                      <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', getColorClasses(selectedAgent.color).light, getColorClasses(selectedAgent.color).text]">
                        {{ selectedAgent.badge }}
                      </span>
                      <span :class="[
                        'flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium border',
                        getProductionStatusClasses(selectedAgent.productionStatus).bg,
                        getProductionStatusClasses(selectedAgent.productionStatus).text,
                        getProductionStatusClasses(selectedAgent.productionStatus).border
                      ]">
                        <svg v-if="selectedAgent.productionStatus === 'production'" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <svg v-else-if="selectedAgent.productionStatus === 'beta'" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
                        </svg>
                        <svg v-else class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        {{ getProductionStatusClasses(selectedAgent.productionStatus).label }}
                      </span>
                    </div>
                  </div>
                </div>
                <button @click="closeDetail" class="p-2 hover:bg-slate-100 rounded-lg transition-colors">
                  <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Modal Body -->
            <div class="p-6 space-y-6">
              <!-- Description -->
              <div>
                <h3 class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">About</h3>
                <p class="text-slate-700">{{ selectedAgent.longDescription }}</p>
              </div>

              <!-- Completion Progress -->
              <div class="p-4 bg-slate-50 rounded-xl">
                <div class="flex items-center justify-between mb-2">
                  <p class="text-sm font-medium text-slate-600">Development Progress</p>
                  <span :class="[
                    'text-lg font-bold',
                    selectedAgent.completionPercent >= 90 ? 'text-emerald-600' :
                    selectedAgent.completionPercent >= 50 ? 'text-amber-600' : 'text-slate-500'
                  ]">{{ selectedAgent.completionPercent }}%</span>
                </div>
                <div class="h-2.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    :class="[
                      'h-full rounded-full transition-all',
                      selectedAgent.completionPercent >= 90 ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' :
                      selectedAgent.completionPercent >= 50 ? 'bg-gradient-to-r from-amber-500 to-amber-400' :
                      'bg-gradient-to-r from-slate-400 to-slate-300'
                    ]"
                    :style="{ width: `${selectedAgent.completionPercent}%` }"
                  ></div>
                </div>
              </div>

              <!-- Stats -->
              <div class="grid grid-cols-2 gap-4">
                <div class="p-4 bg-slate-50 rounded-xl">
                  <p class="text-sm text-slate-500 mb-1">Last Run</p>
                  <p class="text-lg font-semibold text-slate-800">{{ selectedAgent.lastRun ? formatDate(selectedAgent.lastRun) : 'Not yet run' }}</p>
                </div>
                <div class="p-4 bg-slate-50 rounded-xl">
                  <p class="text-sm text-slate-500 mb-1">Items Processed</p>
                  <p class="text-lg font-semibold text-slate-800">{{ formatNumber(selectedAgent.processedItems) }}</p>
                </div>
              </div>

              <!-- Capabilities -->
              <div>
                <h3 class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Capabilities</h3>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="cap in selectedAgent.capabilities"
                    :key="cap"
                    :class="['px-3 py-1.5 text-sm font-medium rounded-lg', getColorClasses(selectedAgent.color).light, getColorClasses(selectedAgent.color).text]"
                  >
                    {{ cap }}
                  </span>
                </div>
              </div>

              <!-- Tech Stack -->
              <div>
                <h3 class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Tech Stack</h3>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="tech in selectedAgent.techStack"
                    :key="tech"
                    class="px-3 py-1.5 text-sm font-medium bg-slate-100 text-slate-600 rounded-lg"
                  >
                    {{ tech }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Modal Footer -->
            <div class="px-6 py-4 bg-slate-50 border-t border-gray-100 flex items-center justify-between">
              <div class="flex items-center space-x-2 text-sm text-slate-500">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span>Agent configuration is managed by system administrators</span>
              </div>
              <button @click="closeDetail" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-xl transition-colors">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
