<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()

const searchQuery = ref('')
const activeSection = ref<string>('getting-started')

interface DocStep {
  title: string
  description: string
}

interface DocSectionConfig {
  id: string
  translationKey: string
  icon: string
  color: string
  lightBg: string
}

const docSectionConfigs: DocSectionConfig[] = [
  {
    id: 'getting-started',
    translationKey: 'gettingStarted',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    color: 'cyan',
    lightBg: 'bg-cyan-50'
  },
  {
    id: 'connections',
    translationKey: 'databaseConnections',
    icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
    color: 'emerald',
    lightBg: 'bg-emerald-50'
  },
  {
    id: 'migration',
    translationKey: 'migrationGuide',
    icon: 'M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4',
    color: 'blue',
    lightBg: 'bg-blue-50'
  },
  {
    id: 'api',
    translationKey: 'apiReference',
    icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
    color: 'violet',
    lightBg: 'bg-violet-50'
  },
  {
    id: 'best-practices',
    translationKey: 'bestPractices',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    color: 'amber',
    lightBg: 'bg-amber-50'
  },
  {
    id: 'troubleshooting',
    translationKey: 'troubleshooting',
    icon: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    color: 'rose',
    lightBg: 'bg-rose-50'
  }
]

// Helper to get topics array from translations
const getTopics = (translationKey: string): string[] => {
  const topics = tm(`docs.${translationKey}.topics`) as unknown
  if (Array.isArray(topics)) {
    return topics.map((topic: unknown) => typeof topic === 'string' ? topic : String(topic))
  }
  return []
}

// Helper to get steps array from translations
const getSteps = (translationKey: string): DocStep[] => {
  const steps = tm(`docs.${translationKey}.steps`) as unknown
  if (Array.isArray(steps)) {
    return steps.map((step: { title?: unknown; description?: unknown }) => ({
      title: typeof step.title === 'string' ? step.title : String(step.title || ''),
      description: typeof step.description === 'string' ? step.description : String(step.description || '')
    }))
  }
  return []
}

// Build sections dynamically from translations
const docSections = computed(() => {
  return docSectionConfigs.map(config => ({
    ...config,
    title: t(`docs.${config.translationKey}.title`),
    description: t(`docs.${config.translationKey}.description`),
    topics: getTopics(config.translationKey),
    overview: t(`docs.${config.translationKey}.overview`),
    steps: getSteps(config.translationKey)
  }))
})

const filteredSections = computed(() => {
  if (!searchQuery.value) return docSections.value
  const query = searchQuery.value.toLowerCase()
  return docSections.value.filter(section =>
    section.title.toLowerCase().includes(query) ||
    section.description.toLowerCase().includes(query) ||
    (Array.isArray(section.topics) && section.topics.some((topic: string) => topic.toLowerCase().includes(query)))
  )
})

const currentSection = computed(() => {
  const section = docSections.value.find(s => s.id === activeSection.value)
  return section ?? docSections.value[0] ?? {
    id: '',
    translationKey: '',
    icon: '',
    color: 'cyan',
    lightBg: 'bg-cyan-50',
    title: '',
    description: '',
    topics: [] as string[],
    overview: '',
    steps: [] as DocStep[]
  }
})

const selectSection = (sectionId: string) => {
  activeSection.value = sectionId
}

const getColorClasses = (color: string, type: 'bg' | 'text' | 'border' | 'ring' | 'light') => {
  const colors: Record<string, Record<string, string>> = {
    cyan: { bg: 'bg-cyan-500', text: 'text-cyan-600', border: 'border-cyan-500', ring: 'ring-cyan-500/20', light: 'bg-cyan-50' },
    emerald: { bg: 'bg-emerald-500', text: 'text-emerald-600', border: 'border-emerald-500', ring: 'ring-emerald-500/20', light: 'bg-emerald-50' },
    blue: { bg: 'bg-blue-500', text: 'text-blue-600', border: 'border-blue-500', ring: 'ring-blue-500/20', light: 'bg-blue-50' },
    violet: { bg: 'bg-violet-500', text: 'text-violet-600', border: 'border-violet-500', ring: 'ring-violet-500/20', light: 'bg-violet-50' },
    amber: { bg: 'bg-amber-500', text: 'text-amber-600', border: 'border-amber-500', ring: 'ring-amber-500/20', light: 'bg-amber-50' },
    rose: { bg: 'bg-rose-500', text: 'text-rose-600', border: 'border-rose-500', ring: 'ring-rose-500/20', light: 'bg-rose-50' }
  }
  return colors[color]?.[type] || ''
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/30">
    <!-- Top Header Bar -->
    <div class="border-b border-gray-200 bg-white/80 backdrop-blur-xl sticky top-0 z-30 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
              </div>
              <div>
                <span class="text-xl font-bold text-gray-900">{{ t('docs.title') }}</span>
                <p class="text-xs text-gray-500">{{ t('docs.subtitle') }}</p>
              </div>
            </div>
          </div>

          <!-- Search Bar -->
          <div class="flex-1 max-w-xl mx-8">
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </div>
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="t('docs.searchPlaceholder')"
                class="block w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500 focus:bg-white transition-all"
              />
              <div class="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
                <kbd class="hidden sm:inline-flex items-center px-2 py-1 text-xs font-medium text-gray-400 bg-gray-100 rounded-md border border-gray-200">⌘K</kbd>
              </div>
            </div>
          </div>

          <div class="flex items-center space-x-4">
            <a
              href="mailto:support@datamigrate.ai"
              class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-medium rounded-lg hover:from-cyan-600 hover:to-blue-700 transition-all shadow-md shadow-cyan-500/25"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
              {{ t('docs.contactSupport') }}
            </a>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex gap-8">
        <!-- Sidebar Navigation -->
        <aside class="hidden lg:block w-72 flex-shrink-0">
          <nav class="sticky top-24">
            <!-- Section List -->
            <div class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div class="p-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
                <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Documentation
                </h3>
              </div>
              <div class="p-2">
                <button
                  v-for="section in filteredSections"
                  :key="section.id"
                  @click="selectSection(section.id)"
                  :class="[
                    'w-full flex items-center space-x-3 px-3 py-3 rounded-xl text-left transition-all duration-200',
                    activeSection === section.id
                      ? `${getColorClasses(section.color, 'light')} border-2 ${getColorClasses(section.color, 'border')}`
                      : 'hover:bg-gray-50 border-2 border-transparent'
                  ]"
                >
                  <div :class="[
                    'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all shadow-sm',
                    activeSection === section.id
                      ? `${getColorClasses(section.color, 'bg')} shadow-lg`
                      : 'bg-gray-100'
                  ]">
                    <svg :class="[
                      'w-5 h-5 transition-colors',
                      activeSection === section.id ? 'text-white' : 'text-gray-500'
                    ]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="section.icon"/>
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <span :class="[
                      'text-sm font-semibold block truncate',
                      activeSection === section.id ? getColorClasses(section.color, 'text') : 'text-gray-700'
                    ]">{{ section.title }}</span>
                    <span class="text-xs text-gray-400 truncate block">{{ section.topics.length }} topics</span>
                  </div>
                  <svg v-if="activeSection === section.id" :class="['w-5 h-5', getColorClasses(section.color, 'text')]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Quick Links Card -->
            <div class="mt-6 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl p-5 text-white shadow-xl shadow-cyan-500/25">
              <div class="flex items-center space-x-3 mb-4">
                <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
                <div>
                  <h4 class="font-semibold">{{ t('docs.needMoreHelp') }}</h4>
                  <p class="text-xs text-cyan-100">24/7 AI Support</p>
                </div>
              </div>
              <p class="text-sm text-cyan-100 mb-4">{{ t('docs.aiSupportAvailable') }}</p>
              <a href="#" class="block w-full py-2.5 bg-white text-cyan-600 text-center text-sm font-semibold rounded-lg hover:bg-cyan-50 transition-colors">
                Open Chat Support
              </a>
            </div>
          </nav>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 min-w-0">
          <!-- Mobile Section Selector -->
          <div class="lg:hidden mb-6">
            <select
              v-model="activeSection"
              class="w-full bg-white border border-gray-200 rounded-xl px-4 py-3 text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 shadow-sm"
            >
              <option v-for="section in filteredSections" :key="section.id" :value="section.id">
                {{ section.title }}
              </option>
            </select>
          </div>

          <!-- Content Area -->
          <div class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <!-- Section Header -->
            <div :class="['p-8 border-b border-gray-100', getColorClasses(currentSection.color, 'light')]">
              <div class="flex items-start space-x-5">
                <div :class="[
                  'w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg',
                  getColorClasses(currentSection.color, 'bg')
                ]" :style="{ boxShadow: `0 10px 40px -10px ${currentSection.color === 'cyan' ? 'rgb(6 182 212 / 0.5)' : currentSection.color === 'emerald' ? 'rgb(16 185 129 / 0.5)' : currentSection.color === 'blue' ? 'rgb(59 130 246 / 0.5)' : currentSection.color === 'violet' ? 'rgb(139 92 246 / 0.5)' : currentSection.color === 'amber' ? 'rgb(245 158 11 / 0.5)' : 'rgb(244 63 94 / 0.5)'}` }">
                  <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="currentSection.icon"/>
                  </svg>
                </div>
                <div class="flex-1">
                  <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ currentSection.title }}</h1>
                  <p class="text-gray-600 text-base leading-relaxed">{{ currentSection.description }}</p>

                  <!-- Topics Tags -->
                  <div class="mt-4 flex flex-wrap gap-2">
                    <span
                      v-for="(topic, index) in currentSection.topics"
                      :key="index"
                      :class="[
                        'inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium',
                        getColorClasses(currentSection.color, 'light'),
                        getColorClasses(currentSection.color, 'text')
                      ]"
                    >
                      <svg class="w-3 h-3 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                      </svg>
                      {{ topic }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Overview -->
            <div class="p-8 border-b border-gray-100 bg-gradient-to-r from-blue-50/50 to-transparent">
              <div class="flex items-start space-x-4">
                <div class="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-2">Overview</h3>
                  <p class="text-gray-600 leading-relaxed">{{ currentSection.overview }}</p>
                </div>
              </div>
            </div>

            <!-- Steps -->
            <div class="p-8">
              <h3 class="text-lg font-bold text-gray-900 mb-6 flex items-center">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mr-3 shadow-lg shadow-cyan-500/25">
                  <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
                  </svg>
                </div>
                Step-by-Step Guide
              </h3>

              <div class="space-y-4">
                <div
                  v-for="(step, index) in currentSection.steps"
                  :key="index"
                  class="group relative"
                >
                  <!-- Connecting Line -->
                  <div
                    v-if="index < currentSection.steps.length - 1"
                    :class="['absolute left-6 top-16 w-0.5 h-full', getColorClasses(currentSection.color, 'bg'), 'opacity-20']"
                  ></div>

                  <div class="relative flex items-start space-x-4 p-5 rounded-xl bg-gray-50 border border-gray-100 hover:border-gray-200 hover:bg-white hover:shadow-md transition-all duration-200">
                    <!-- Step Number -->
                    <div :class="[
                      'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 text-base font-bold text-white shadow-lg',
                      getColorClasses(currentSection.color, 'bg')
                    ]" :style="{ boxShadow: `0 8px 24px -8px ${currentSection.color === 'cyan' ? 'rgb(6 182 212 / 0.5)' : currentSection.color === 'emerald' ? 'rgb(16 185 129 / 0.5)' : currentSection.color === 'blue' ? 'rgb(59 130 246 / 0.5)' : currentSection.color === 'violet' ? 'rgb(139 92 246 / 0.5)' : currentSection.color === 'amber' ? 'rgb(245 158 11 / 0.5)' : 'rgb(244 63 94 / 0.5)'}` }">
                      {{ index + 1 }}
                    </div>

                    <!-- Step Content -->
                    <div class="flex-1 min-w-0">
                      <h4 class="text-base font-semibold text-gray-900 mb-2">{{ step.title }}</h4>
                      <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{{ step.description }}</p>
                    </div>

                    <!-- Arrow Icon -->
                    <div class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', getColorClasses(currentSection.color, 'light')]">
                        <svg :class="['w-4 h-4', getColorClasses(currentSection.color, 'text')]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Navigation Cards -->
          <div class="mt-8">
            <h3 class="text-lg font-bold text-gray-900 mb-4">Explore More Topics</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <template v-for="section in filteredSections" :key="section.id">
                <button
                  v-if="section.id !== activeSection"
                  @click="selectSection(section.id)"
                  class="group p-5 rounded-xl bg-white border border-gray-200 hover:border-gray-300 hover:shadow-lg text-left transition-all duration-200"
                >
                  <div class="flex items-center space-x-4">
                    <div :class="[
                      'w-12 h-12 rounded-xl flex items-center justify-center transition-all',
                      getColorClasses(section.color, 'light'),
                      'group-hover:' + getColorClasses(section.color, 'bg')
                    ]">
                      <svg :class="['w-6 h-6 transition-colors', getColorClasses(section.color, 'text'), 'group-hover:text-white']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="section.icon"/>
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h4 class="text-sm font-semibold text-gray-900 group-hover:text-gray-900">{{ section.title }}</h4>
                      <p class="text-xs text-gray-500 truncate">{{ section.description }}</p>
                    </div>
                    <svg class="w-5 h-5 text-gray-300 group-hover:text-gray-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                  </div>
                </button>
              </template>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar for webkit browsers */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgb(243 244 246);
}

::-webkit-scrollbar-thumb {
  background: rgb(209 213 219);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgb(156 163 175);
}

/* Smooth transitions */
* {
  scroll-behavior: smooth;
}
</style>
