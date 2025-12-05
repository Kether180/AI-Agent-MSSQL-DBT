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
}

const docSectionConfigs: DocSectionConfig[] = [
  {
    id: 'getting-started',
    translationKey: 'gettingStarted',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    color: 'cyan'
  },
  {
    id: 'connections',
    translationKey: 'databaseConnections',
    icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
    color: 'emerald'
  },
  {
    id: 'migration',
    translationKey: 'migrationGuide',
    icon: 'M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4',
    color: 'blue'
  },
  {
    id: 'api',
    translationKey: 'apiReference',
    icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
    color: 'violet'
  },
  {
    id: 'best-practices',
    translationKey: 'bestPractices',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    color: 'amber'
  },
  {
    id: 'troubleshooting',
    translationKey: 'troubleshooting',
    icon: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    color: 'rose'
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

const getColorClasses = (color: string, type: 'bg' | 'text' | 'border' | 'ring') => {
  const colors: Record<string, Record<string, string>> = {
    cyan: { bg: 'bg-cyan-500', text: 'text-cyan-500', border: 'border-cyan-500', ring: 'ring-cyan-500/20' },
    emerald: { bg: 'bg-emerald-500', text: 'text-emerald-500', border: 'border-emerald-500', ring: 'ring-emerald-500/20' },
    blue: { bg: 'bg-blue-500', text: 'text-blue-500', border: 'border-blue-500', ring: 'ring-blue-500/20' },
    violet: { bg: 'bg-violet-500', text: 'text-violet-500', border: 'border-violet-500', ring: 'ring-violet-500/20' },
    amber: { bg: 'bg-amber-500', text: 'text-amber-500', border: 'border-amber-500', ring: 'ring-amber-500/20' },
    rose: { bg: 'bg-rose-500', text: 'text-rose-500', border: 'border-rose-500', ring: 'ring-rose-500/20' }
  }
  return colors[color]?.[type] || ''
}
</script>

<template>
  <div class="min-h-screen bg-slate-950">
    <!-- Top Header Bar -->
    <div class="border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
              </div>
              <span class="text-lg font-semibold text-white">{{ t('docs.title') }}</span>
            </div>
          </div>

          <!-- Search Bar -->
          <div class="flex-1 max-w-xl mx-8">
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </div>
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="t('docs.searchPlaceholder')"
                class="block w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-300 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500 transition-all"
              />
              <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <kbd class="hidden sm:inline-flex items-center px-2 py-0.5 text-xs font-mono text-slate-500 bg-slate-800 rounded">⌘K</kbd>
              </div>
            </div>
          </div>

          <div class="flex items-center space-x-3">
            <a
              href="mailto:support@datamigrate.ai"
              class="text-sm text-slate-400 hover:text-white transition-colors"
            >
              {{ t('docs.contactSupport') }}
            </a>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex gap-8">
        <!-- Sidebar Navigation -->
        <aside class="hidden lg:block w-64 flex-shrink-0">
          <nav class="sticky top-24 space-y-1">
            <div class="mb-4">
              <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                Documentation
              </h3>
            </div>
            <button
              v-for="section in filteredSections"
              :key="section.id"
              @click="selectSection(section.id)"
              :class="[
                'w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-left transition-all duration-150',
                activeSection === section.id
                  ? 'bg-slate-800/80 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              ]"
            >
              <div :class="[
                'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors',
                activeSection === section.id ? getColorClasses(section.color, 'bg') : 'bg-slate-800'
              ]">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="section.icon"/>
                </svg>
              </div>
              <span class="text-sm font-medium truncate">{{ section.title }}</span>
            </button>

            <!-- Quick Links -->
            <div class="pt-6 mt-6 border-t border-slate-800">
              <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                Resources
              </h3>
              <a href="#" class="flex items-center space-x-2 px-3 py-2 text-slate-400 hover:text-white text-sm transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                </svg>
                <span>API Status</span>
              </a>
              <a href="#" class="flex items-center space-x-2 px-3 py-2 text-slate-400 hover:text-white text-sm transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
                <span>Community</span>
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
              class="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
              <option v-for="section in filteredSections" :key="section.id" :value="section.id">
                {{ section.title }}
              </option>
            </select>
          </div>

          <!-- Content Area -->
          <div class="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden">
            <!-- Section Header -->
            <div class="p-8 border-b border-slate-800">
              <div class="flex items-start space-x-4">
                <div :class="[
                  'w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0',
                  getColorClasses(currentSection.color, 'bg')
                ]">
                  <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="currentSection.icon"/>
                  </svg>
                </div>
                <div class="flex-1">
                  <h1 class="text-2xl font-bold text-white mb-2">{{ currentSection.title }}</h1>
                  <p class="text-slate-400 text-base leading-relaxed">{{ currentSection.description }}</p>
                </div>
              </div>

              <!-- Topics Tags -->
              <div class="mt-6 flex flex-wrap gap-2">
                <span
                  v-for="(topic, index) in currentSection.topics"
                  :key="index"
                  class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700"
                >
                  {{ topic }}
                </span>
              </div>
            </div>

            <!-- Overview -->
            <div class="p-8 border-b border-slate-800 bg-gradient-to-r from-slate-900/50 to-transparent">
              <div class="flex items-start space-x-3">
                <div class="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center flex-shrink-0">
                  <svg class="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-2">Overview</h3>
                  <p class="text-slate-400 leading-relaxed">{{ currentSection.overview }}</p>
                </div>
              </div>
            </div>

            <!-- Steps -->
            <div class="p-8">
              <h3 class="text-lg font-semibold text-white mb-6 flex items-center">
                <svg class="w-5 h-5 mr-2 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
                </svg>
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
                    class="absolute left-5 top-14 w-0.5 h-full bg-gradient-to-b from-slate-700 to-transparent"
                  ></div>

                  <div class="relative flex items-start space-x-4 p-4 rounded-xl bg-slate-800/30 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/50 transition-all duration-200">
                    <!-- Step Number -->
                    <div :class="[
                      'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 text-sm font-bold text-white',
                      getColorClasses(currentSection.color, 'bg')
                    ]">
                      {{ index + 1 }}
                    </div>

                    <!-- Step Content -->
                    <div class="flex-1 min-w-0">
                      <h4 class="text-base font-semibold text-white mb-1">{{ step.title }}</h4>
                      <p class="text-sm text-slate-400 leading-relaxed whitespace-pre-line">{{ step.description }}</p>
                    </div>

                    <!-- Arrow Icon -->
                    <div class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Helpful Links Footer -->
            <div class="p-6 bg-slate-800/30 border-t border-slate-800">
              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div class="flex items-center space-x-2 text-slate-400 text-sm">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <span>{{ t('docs.needMoreHelp') }}</span>
                </div>
                <div class="flex items-center space-x-3">
                  <a
                    href="mailto:support@datamigrate.ai"
                    class="inline-flex items-center px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white text-sm font-medium rounded-lg transition-colors"
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

          <!-- Quick Navigation Cards -->
          <div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
            <template v-for="section in filteredSections" :key="section.id">
              <button
                v-if="section.id !== activeSection"
                @click="selectSection(section.id)"
                class="group p-5 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/50 text-left transition-all duration-200"
              >
                <div class="flex items-center space-x-3">
                  <div :class="[
                    'w-10 h-10 rounded-lg flex items-center justify-center',
                    'bg-slate-800 group-hover:' + getColorClasses(section.color, 'bg')
                  ]">
                    <svg :class="['w-5 h-5 text-slate-400 group-hover:text-white transition-colors']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="section.icon"/>
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <h4 class="text-sm font-semibold text-white truncate">{{ section.title }}</h4>
                    <p class="text-xs text-slate-500 truncate">{{ section.description }}</p>
                  </div>
                  <svg class="w-5 h-5 text-slate-600 group-hover:text-slate-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                  </svg>
                </div>
              </button>
            </template>
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
  background: rgb(15 23 42);
}

::-webkit-scrollbar-thumb {
  background: rgb(51 65 85);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgb(71 85 105);
}

/* Smooth transitions */
* {
  scroll-behavior: smooth;
}
</style>
