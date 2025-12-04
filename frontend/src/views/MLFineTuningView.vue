<script setup lang="ts">
import { ref, computed } from 'vue'
import { platformLogos } from '@/assets/logos'

// Target platforms for ML models
const targetPlatforms = ref([
  { id: 'snowflake', name: 'Snowflake', description: 'Cloud data warehouse' },
  { id: 'bigquery', name: 'BigQuery', description: 'Google Cloud analytics' },
  { id: 'databricks', name: 'Databricks', description: 'Unified ML/AI platform' },
  { id: 'redshift', name: 'Redshift', description: 'AWS data warehouse' },
  { id: 'fabric', name: 'Microsoft Fabric', description: 'Microsoft analytics SaaS' }
])

// Sample data for demonstration
const models = ref([
  { id: 1, name: 'Schema Analyzer', type: 'classification', status: 'trained', accuracy: 94.2, lastTrained: '2024-01-15' },
  { id: 2, name: 'Data Type Predictor', type: 'classification', status: 'training', accuracy: 0, lastTrained: null },
  { id: 3, name: 'Relationship Detector', type: 'clustering', status: 'ready', accuracy: 89.7, lastTrained: '2024-01-10' }
])

const trainingJobs = ref([
  { id: 1, model: 'Schema Analyzer', status: 'completed', progress: 100, epochs: 50, startTime: '2024-01-15 10:30' },
  { id: 2, model: 'Data Type Predictor', status: 'running', progress: 67, epochs: 100, startTime: '2024-01-16 14:00' },
  { id: 3, model: 'Entity Matcher', status: 'queued', progress: 0, epochs: 75, startTime: null }
])

const datasets = ref([
  { id: 1, name: 'Migration Patterns v2', records: 15420, features: 24, status: 'validated' },
  { id: 2, name: 'Schema Mappings', records: 8750, features: 18, status: 'processing' },
  { id: 3, name: 'Data Quality Metrics', records: 32100, features: 31, status: 'validated' }
])

const metrics = ref({
  modelsDeployed: 12,
  avgAccuracy: 91.4,
  trainingHours: 156,
  predictions: '2.4M'
})

const selectedModel = ref<number | null>(null)
const showTrainModal = ref(false)

const newTrainingJob = ref({
  modelId: null as number | null,
  datasetId: null as number | null,
  epochs: 50,
  learningRate: 0.001,
  batchSize: 32
})

const runningJobsCount = computed(() => trainingJobs.value.filter(j => j.status === 'running').length)

const getStatusColor = (status: string) => {
  switch (status) {
    case 'trained':
    case 'completed':
    case 'validated':
      return 'bg-emerald-100 text-emerald-700'
    case 'training':
    case 'running':
    case 'processing':
      return 'bg-indigo-100 text-indigo-700'
    case 'ready':
    case 'queued':
      return 'bg-slate-100 text-slate-600'
    default:
      return 'bg-slate-100 text-slate-600'
  }
}

const startTraining = () => {
  if (!newTrainingJob.value.modelId || !newTrainingJob.value.datasetId) return

  const model = models.value.find(m => m.id === newTrainingJob.value.modelId)
  trainingJobs.value.unshift({
    id: Date.now(),
    model: model?.name || 'Unknown',
    status: 'running',
    progress: 0,
    epochs: newTrainingJob.value.epochs,
    startTime: new Date().toISOString().slice(0, 16).replace('T', ' ')
  })

  // Simulate training progress
  const job = trainingJobs.value[0]
  const interval = setInterval(() => {
    if (job.progress < 100) {
      job.progress += Math.random() * 5
      if (job.progress >= 100) {
        job.progress = 100
        job.status = 'completed'
        clearInterval(interval)
      }
    }
  }, 500)

  showTrainModal.value = false
  newTrainingJob.value = {
    modelId: null,
    datasetId: null,
    epochs: 50,
    learningRate: 0.001,
    batchSize: 32
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-indigo-50">
    <!-- Header -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-8">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div class="w-14 h-14 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30 mr-4">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                </svg>
              </div>
              <div>
                <h1 class="text-3xl font-bold text-white">
                  ML Fine-Tuning <span class="bg-gradient-to-r from-indigo-400 to-blue-400 bg-clip-text text-transparent">Agent</span>
                </h1>
                <p class="mt-1 text-slate-300">
                  Train and optimize AI models for data migration
                </p>
              </div>
            </div>
            <button
              @click="showTrainModal = true"
              class="inline-flex items-center px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:from-indigo-600 hover:to-blue-700 transition-all duration-200"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
              Start Training
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <div class="max-w-7xl mx-auto">
        <!-- Metrics Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div class="bg-white/80 backdrop-blur-sm rounded-xl p-5 border border-slate-200/50 shadow-lg">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-slate-500">Models Deployed</p>
                <p class="text-3xl font-bold text-slate-800 mt-1">{{ metrics.modelsDeployed }}</p>
              </div>
              <div class="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
                <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                </svg>
              </div>
            </div>
          </div>

          <div class="bg-white/80 backdrop-blur-sm rounded-xl p-5 border border-slate-200/50 shadow-lg">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-slate-500">Avg Accuracy</p>
                <p class="text-3xl font-bold text-slate-800 mt-1">{{ metrics.avgAccuracy }}%</p>
              </div>
              <div class="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
            </div>
          </div>

          <div class="bg-white/80 backdrop-blur-sm rounded-xl p-5 border border-slate-200/50 shadow-lg">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-slate-500">Training Hours</p>
                <p class="text-3xl font-bold text-slate-800 mt-1">{{ metrics.trainingHours }}</p>
              </div>
              <div class="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
            </div>
          </div>

          <div class="bg-white/80 backdrop-blur-sm rounded-xl p-5 border border-slate-200/50 shadow-lg">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-slate-500">Predictions</p>
                <p class="text-3xl font-bold text-slate-800 mt-1">{{ metrics.predictions }}</p>
              </div>
              <div class="w-12 h-12 bg-cyan-100 rounded-xl flex items-center justify-center">
                <svg class="w-6 h-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Models Panel -->
          <div class="bg-white/80 backdrop-blur-sm rounded-xl border border-slate-200/50 shadow-lg overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-200 bg-slate-50/50">
              <h3 class="text-lg font-semibold text-slate-800 flex items-center">
                <svg class="w-5 h-5 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                </svg>
                AI Models
              </h3>
            </div>
            <div class="p-4 space-y-3">
              <div
                v-for="model in models"
                :key="model.id"
                @click="selectedModel = model.id"
                :class="[
                  'p-4 rounded-lg border-2 cursor-pointer transition-all duration-200',
                  selectedModel === model.id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                ]"
              >
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center">
                    <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-lg flex items-center justify-center mr-3 shadow-lg shadow-indigo-500/20">
                      <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                      </svg>
                    </div>
                    <div>
                      <p class="font-medium text-slate-800">{{ model.name }}</p>
                      <p class="text-xs text-slate-500 capitalize">{{ model.type }}</p>
                    </div>
                  </div>
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(model.status)]">
                    {{ model.status }}
                  </span>
                </div>
                <div v-if="model.accuracy > 0" class="flex items-center justify-between text-sm">
                  <span class="text-slate-500">Accuracy</span>
                  <span class="font-semibold text-slate-700">{{ model.accuracy }}%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Training Jobs Panel -->
          <div class="bg-white/80 backdrop-blur-sm rounded-xl border border-slate-200/50 shadow-lg overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <h3 class="text-lg font-semibold text-slate-800 flex items-center">
                <svg class="w-5 h-5 mr-2 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
                Training Jobs
              </h3>
              <span v-if="runningJobsCount > 0" class="px-3 py-1 text-sm font-medium rounded-full bg-indigo-100 text-indigo-700">
                {{ runningJobsCount }} running
              </span>
            </div>
            <div class="p-4 space-y-3">
              <div
                v-for="job in trainingJobs"
                :key="job.id"
                class="p-4 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors"
              >
                <div class="flex items-center justify-between mb-3">
                  <div>
                    <p class="font-medium text-slate-800">{{ job.model }}</p>
                    <p class="text-xs text-slate-500">{{ job.epochs }} epochs</p>
                  </div>
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(job.status)]">
                    {{ job.status }}
                  </span>
                </div>
                <div class="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    :class="[
                      'h-full rounded-full transition-all duration-300',
                      job.status === 'completed' ? 'bg-emerald-500' : 'bg-gradient-to-r from-indigo-500 to-blue-500'
                    ]"
                    :style="{ width: `${job.progress}%` }"
                  ></div>
                </div>
                <div class="flex justify-between mt-2 text-xs text-slate-500">
                  <span>{{ job.startTime || 'Queued' }}</span>
                  <span>{{ Math.round(job.progress) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Datasets Panel -->
        <div class="mt-8 bg-white/80 backdrop-blur-sm rounded-xl border border-slate-200/50 shadow-lg overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-200 bg-slate-50/50">
            <h3 class="text-lg font-semibold text-slate-800 flex items-center">
              <svg class="w-5 h-5 mr-2 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
              </svg>
              Training Datasets
            </h3>
          </div>
          <div class="p-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div
                v-for="dataset in datasets"
                :key="dataset.id"
                class="p-4 rounded-lg border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-all"
              >
                <div class="flex items-center justify-between mb-3">
                  <p class="font-medium text-slate-800">{{ dataset.name }}</p>
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(dataset.status)]">
                    {{ dataset.status }}
                  </span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p class="text-slate-500">Records</p>
                    <p class="font-semibold text-slate-700">{{ dataset.records.toLocaleString() }}</p>
                  </div>
                  <div>
                    <p class="text-slate-500">Features</p>
                    <p class="font-semibold text-slate-700">{{ dataset.features }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Target Platforms Panel -->
        <div class="mt-8 bg-white/80 backdrop-blur-sm rounded-xl border border-slate-200/50 shadow-lg overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-200 bg-slate-50/50">
            <h3 class="text-lg font-semibold text-slate-800 flex items-center">
              <svg class="w-5 h-5 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
              </svg>
              Supported Target Platforms
            </h3>
            <p class="text-sm text-slate-500 mt-1">ML models optimized for these data warehouses</p>
          </div>
          <div class="p-4">
            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div
                v-for="platform in targetPlatforms"
                :key="platform.id"
                class="p-4 rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 transition-all duration-200 text-center cursor-pointer group"
              >
                <div class="w-12 h-12 mx-auto mb-3 bg-white rounded-xl border border-slate-200 flex items-center justify-center group-hover:border-indigo-300 group-hover:shadow-lg transition-all">
                  <img
                    :src="platformLogos[platform.id]"
                    :alt="platform.name"
                    class="w-8 h-8"
                  />
                </div>
                <p class="font-medium text-slate-800 text-sm">{{ platform.name }}</p>
                <p class="text-xs text-slate-500 mt-1">{{ platform.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Train Modal -->
    <div v-if="showTrainModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="showTrainModal = false"></div>
        <div class="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6">
          <h3 class="text-xl font-semibold text-slate-800 mb-6">Start Training Job</h3>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Model</label>
              <select
                v-model="newTrainingJob.modelId"
                class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option :value="null" disabled>Select a model</option>
                <option v-for="model in models" :key="model.id" :value="model.id">
                  {{ model.name }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Dataset</label>
              <select
                v-model="newTrainingJob.datasetId"
                class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option :value="null" disabled>Select a dataset</option>
                <option v-for="dataset in datasets" :key="dataset.id" :value="dataset.id">
                  {{ dataset.name }} ({{ dataset.records.toLocaleString() }} records)
                </option>
              </select>
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Epochs</label>
                <input
                  v-model.number="newTrainingJob.epochs"
                  type="number"
                  min="1"
                  class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Learning Rate</label>
                <input
                  v-model.number="newTrainingJob.learningRate"
                  type="number"
                  step="0.0001"
                  class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Batch Size</label>
                <input
                  v-model.number="newTrainingJob.batchSize"
                  type="number"
                  min="1"
                  class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button
              @click="showTrainModal = false"
              class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              @click="startTraining"
              :disabled="!newTrainingJob.modelId || !newTrainingJob.datasetId"
              class="px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 text-white font-medium rounded-lg shadow-lg hover:from-indigo-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              Start Training
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
