<script setup lang="ts">
import { ref, computed } from 'vue'
import { platformLogos } from '@/assets/logos'

// Sample data for demonstration
const dataSources = ref([
  { id: 1, name: 'Sales Database', type: 'mssql', status: 'connected', tables: 24 },
  { id: 2, name: 'Customer Excel', type: 'excel', status: 'pending', tables: 3 },
  { id: 3, name: 'Inventory Data', type: 'mssql', status: 'connected', tables: 12 }
])

const prepTasks = ref([
  { id: 1, name: 'Clean Customer Names', status: 'completed', progress: 100, type: 'cleaning' },
  { id: 2, name: 'Normalize Address Fields', status: 'running', progress: 67, type: 'normalization' },
  { id: 3, name: 'Remove Duplicates', status: 'pending', progress: 0, type: 'deduplication' },
  { id: 4, name: 'Data Type Conversion', status: 'pending', progress: 0, type: 'transformation' }
])

const qualityMetrics = ref({
  completeness: 94,
  accuracy: 87,
  consistency: 91,
  uniqueness: 98
})

const selectedSource = ref<number | null>(null)
const isProcessing = ref(false)
const showNewTaskModal = ref(false)

const newTask = ref({
  name: '',
  type: 'cleaning',
  sourceId: null as number | null,
  options: {
    removeNulls: true,
    trimWhitespace: true,
    standardizeCase: false
  }
})

const taskTypes = [
  { value: 'cleaning', label: 'Data Cleaning', icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16' },
  { value: 'normalization', label: 'Normalization', icon: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z' },
  { value: 'deduplication', label: 'Deduplication', icon: 'M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z' },
  { value: 'transformation', label: 'Transformation', icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' },
  { value: 'validation', label: 'Validation', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' }
]

const runningTasksCount = computed(() => prepTasks.value.filter(t => t.status === 'running').length)

const startTask = (taskId: number) => {
  const task = prepTasks.value.find(t => t.id === taskId)
  if (task) {
    task.status = 'running'
    // Simulate progress
    const interval = setInterval(() => {
      if (task.progress < 100) {
        task.progress += Math.random() * 15
        if (task.progress >= 100) {
          task.progress = 100
          task.status = 'completed'
          clearInterval(interval)
        }
      }
    }, 500)
  }
}

const createTask = () => {
  if (!newTask.value.name || !newTask.value.sourceId) return

  prepTasks.value.push({
    id: Date.now(),
    name: newTask.value.name,
    status: 'pending',
    progress: 0,
    type: newTask.value.type
  })

  newTask.value = {
    name: '',
    type: 'cleaning',
    sourceId: null,
    options: {
      removeNulls: true,
      trimWhitespace: true,
      standardizeCase: false
    }
  }
  showNewTaskModal.value = false
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'bg-emerald-100 text-emerald-700'
    case 'running': return 'bg-cyan-100 text-cyan-700'
    case 'pending': return 'bg-slate-100 text-slate-600'
    case 'connected': return 'bg-emerald-100 text-emerald-700'
    default: return 'bg-slate-100 text-slate-600'
  }
}

const getQualityColor = (value: number) => {
  if (value >= 90) return 'from-emerald-500 to-green-500'
  if (value >= 70) return 'from-amber-500 to-yellow-500'
  return 'from-red-500 to-rose-500'
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-cyan-50">
    <!-- Header -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-8">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div class="w-14 h-14 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/30 mr-4">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                </svg>
              </div>
              <div>
                <h1 class="text-3xl font-bold text-white">
                  DataPrep <span class="bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">AI Agent</span>
                </h1>
                <p class="mt-1 text-slate-300">
                  Intelligent data preparation, cleaning, and transformation
                </p>
              </div>
            </div>
            <button
              @click="showNewTaskModal = true"
              class="inline-flex items-center px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-medium rounded-xl shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50 hover:from-emerald-600 hover:to-teal-700 transition-all duration-200"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
              </svg>
              New Prep Task
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <div class="max-w-7xl mx-auto">
        <!-- Data Quality Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div
            v-for="(value, key) in qualityMetrics"
            :key="key"
            class="bg-white/80 backdrop-blur-sm rounded-xl p-5 border border-slate-200/50 shadow-lg"
          >
            <div class="flex items-center justify-between mb-3">
              <span class="text-sm font-medium text-slate-600 capitalize">{{ key }}</span>
              <span class="text-2xl font-bold text-slate-800">{{ value }}%</span>
            </div>
            <div class="h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                :class="['h-full rounded-full bg-gradient-to-r transition-all duration-500', getQualityColor(value)]"
                :style="{ width: `${value}%` }"
              ></div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Data Sources Panel -->
          <div class="bg-white/80 backdrop-blur-sm rounded-xl border border-slate-200/50 shadow-lg overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-200 bg-slate-50/50">
              <h3 class="text-lg font-semibold text-slate-800 flex items-center">
                <svg class="w-5 h-5 mr-2 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                </svg>
                Data Sources
              </h3>
            </div>
            <div class="p-4 space-y-3">
              <div
                v-for="source in dataSources"
                :key="source.id"
                @click="selectedSource = source.id"
                :class="[
                  'p-4 rounded-lg border-2 cursor-pointer transition-all duration-200',
                  selectedSource === source.id
                    ? 'border-emerald-500 bg-emerald-50'
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                ]"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <div class="w-10 h-10 rounded-lg flex items-center justify-center mr-3 bg-white border border-slate-200">
                      <img
                        v-if="platformLogos[source.type]"
                        :src="platformLogos[source.type]"
                        :alt="source.type"
                        class="w-6 h-6"
                      />
                      <svg v-else class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                      </svg>
                    </div>
                    <div>
                      <p class="font-medium text-slate-800">{{ source.name }}</p>
                      <p class="text-xs text-slate-500">{{ source.tables }} tables</p>
                    </div>
                  </div>
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(source.status)]">
                    {{ source.status }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Prep Tasks Panel -->
          <div class="lg:col-span-2 bg-white/80 backdrop-blur-sm rounded-xl border border-slate-200/50 shadow-lg overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <h3 class="text-lg font-semibold text-slate-800 flex items-center">
                <svg class="w-5 h-5 mr-2 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
                </svg>
                Preparation Tasks
              </h3>
              <span v-if="runningTasksCount > 0" class="px-3 py-1 text-sm font-medium rounded-full bg-cyan-100 text-cyan-700">
                {{ runningTasksCount }} running
              </span>
            </div>
            <div class="p-4 space-y-3">
              <div
                v-for="task in prepTasks"
                :key="task.id"
                class="p-4 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors"
              >
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center">
                    <div class="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center mr-3">
                      <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="taskTypes.find(t => t.value === task.type)?.icon || ''"/>
                      </svg>
                    </div>
                    <div>
                      <p class="font-medium text-slate-800">{{ task.name }}</p>
                      <p class="text-xs text-slate-500 capitalize">{{ task.type }}</p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(task.status)]">
                      {{ task.status }}
                    </span>
                    <button
                      v-if="task.status === 'pending'"
                      @click="startTask(task.id)"
                      class="p-2 text-cyan-600 hover:bg-cyan-50 rounded-lg transition-colors"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    :class="[
                      'h-full rounded-full transition-all duration-300',
                      task.status === 'completed' ? 'bg-emerald-500' : 'bg-gradient-to-r from-cyan-500 to-teal-500'
                    ]"
                    :style="{ width: `${task.progress}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI Recommendations -->
        <div class="mt-8 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-xl border border-emerald-200/50 p-6">
          <div class="flex items-start">
            <div class="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg mr-4">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-slate-800 mb-2">AI Recommendations</h3>
              <ul class="space-y-2 text-sm text-slate-600">
                <li class="flex items-center">
                  <svg class="w-4 h-4 mr-2 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                  </svg>
                  Detected 127 potential duplicate records in Customer table - Run deduplication
                </li>
                <li class="flex items-center">
                  <svg class="w-4 h-4 mr-2 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                  </svg>
                  6% null values in Address field - Consider data enrichment
                </li>
                <li class="flex items-center">
                  <svg class="w-4 h-4 mr-2 text-cyan-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                  </svg>
                  Phone numbers have inconsistent formats - Apply standardization
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- New Task Modal -->
    <div v-if="showNewTaskModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="showNewTaskModal = false"></div>
        <div class="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6">
          <h3 class="text-xl font-semibold text-slate-800 mb-6">Create New Prep Task</h3>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Task Name</label>
              <input
                v-model="newTask.name"
                type="text"
                placeholder="e.g., Clean Customer Data"
                class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Task Type</label>
              <select
                v-model="newTask.type"
                class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              >
                <option v-for="type in taskTypes" :key="type.value" :value="type.value">
                  {{ type.label }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Data Source</label>
              <select
                v-model="newTask.sourceId"
                class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              >
                <option :value="null" disabled>Select a data source</option>
                <option v-for="source in dataSources" :key="source.id" :value="source.id">
                  {{ source.name }}
                </option>
              </select>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button
              @click="showNewTaskModal = false"
              class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              @click="createTask"
              :disabled="!newTask.name || !newTask.sourceId"
              class="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-medium rounded-lg shadow-lg hover:from-emerald-600 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              Create Task
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
