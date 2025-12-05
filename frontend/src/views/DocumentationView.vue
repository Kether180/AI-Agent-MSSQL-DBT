<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const searchQuery = ref('')
const activeSection = ref<string | null>(null)

interface DocStep {
  title: string
  description: string
}

interface DocSection {
  id: string
  translationKey: string
  icon: string
  gradient: string
  bgGradient: string
}

const docSectionConfigs: DocSection[] = [
  {
    id: 'getting-started',
    translationKey: 'gettingStarted',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-white to-cyan-50'
  },
  {
    id: 'connections',
    translationKey: 'databaseConnections',
    icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
    gradient: 'from-green-500 to-emerald-600',
    bgGradient: 'from-white to-green-50'
  },
  {
    id: 'migration',
    translationKey: 'migrationGuide',
    icon: 'M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4',
    gradient: 'from-blue-500 to-cyan-600',
    bgGradient: 'from-white to-blue-50'
  },
  {
    id: 'api',
    translationKey: 'apiReference',
    icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
    gradient: 'from-slate-500 to-slate-700',
    bgGradient: 'from-white to-slate-50'
  },
  {
    id: 'best-practices',
    translationKey: 'bestPractices',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    gradient: 'from-amber-500 to-orange-600',
    bgGradient: 'from-white to-amber-50'
  },
  {
    id: 'troubleshooting',
    translationKey: 'troubleshooting',
    icon: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    gradient: 'from-red-500 to-rose-600',
    bgGradient: 'from-white to-red-50'
  }
]

// Build sections dynamically from translations
const docSections = computed(() => {
  return docSectionConfigs.map(config => ({
    ...config,
    title: t(`docs.${config.translationKey}.title`),
    description: t(`docs.${config.translationKey}.description`),
    topics: t(`docs.${config.translationKey}.topics`) as unknown as string[],
    overview: t(`docs.${config.translationKey}.overview`),
    steps: t(`docs.${config.translationKey}.steps`) as unknown as DocStep[]
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

const toggleSection = (sectionId: string) => {
  activeSection.value = activeSection.value === sectionId ? null : sectionId
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-cyan-50">
    <!-- Header -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-8">
          <h1 class="text-3xl font-bold text-white">{{ t('docs.title') }}</h1>
          <p class="mt-2 text-slate-300">
            {{ t('docs.subtitle') }}
          </p>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <!-- Search Bar -->
      <div class="max-w-2xl mx-auto mb-10">
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
            class="block w-full pl-12 pr-4 py-4 border border-gray-200 rounded-2xl leading-5 bg-white placeholder-gray-400 shadow-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-base transition-all duration-200"
          />
        </div>
      </div>

      <!-- Documentation Cards Grid -->
      <div class="space-y-6">
        <div
          v-for="section in filteredSections"
          :key="section.id"
          class="doc-card overflow-hidden shadow-md rounded-xl border border-gray-100 transition-all duration-300"
          :class="[`bg-gradient-to-br ${section.bgGradient}`]"
        >
          <!-- Card Header (Clickable) -->
          <div
            class="p-6 cursor-pointer group"
            @click="toggleSection(section.id)"
          >
            <div class="flex items-start">
              <div :class="[
                'flex-shrink-0 rounded-xl p-3 shadow-lg',
                `bg-gradient-to-br ${section.gradient}`
              ]">
                <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="section.icon"/>
                </svg>
              </div>
              <div class="ml-4 flex-1">
                <h2 class="text-lg font-semibold text-gray-900 group-hover:text-cyan-600 transition-colors">
                  {{ section.title }}
                </h2>
                <p class="mt-1 text-sm text-gray-500">
                  {{ section.description }}
                </p>
              </div>
              <div class="ml-4 flex-shrink-0">
                <svg
                  class="h-6 w-6 text-gray-400 transition-transform duration-300"
                  :class="{ 'rotate-180': activeSection === section.id }"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                </svg>
              </div>
            </div>

            <!-- Topics -->
            <div class="mt-4 flex flex-wrap gap-2">
              <span
                v-for="(topic, index) in section.topics"
                :key="index"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700"
              >
                {{ topic }}
              </span>
            </div>
          </div>

          <!-- Expandable Content -->
          <div
            v-show="activeSection === section.id"
            class="px-6 pb-6 border-t border-gray-200 bg-white/50"
          >
            <div class="pt-6">
              <p class="text-gray-600 mb-6">{{ section.overview }}</p>

              <div class="space-y-4">
                <div
                  v-for="(step, index) in section.steps"
                  :key="index"
                  class="flex items-start p-4 bg-white rounded-lg border border-gray-100 shadow-sm"
                >
                  <div :class="[
                    'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold',
                    `bg-gradient-to-br ${section.gradient}`
                  ]">
                    {{ index + 1 }}
                  </div>
                  <div class="ml-4">
                    <h4 class="font-semibold text-gray-900">{{ step.title }}</h4>
                    <p class="mt-1 text-sm text-gray-600 whitespace-pre-line">{{ step.description }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom border accent -->
          <div :class="[
            'h-1',
            activeSection === section.id ? 'opacity-100' : 'opacity-0',
            `bg-gradient-to-r ${section.gradient}`
          ]"></div>
        </div>
      </div>

      <!-- Quick Help Section -->
      <div class="mt-12 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl p-8 text-white">
        <div class="flex flex-col md:flex-row items-center justify-between">
          <div>
            <h3 class="text-2xl font-bold mb-2">{{ t('docs.needMoreHelp') }}</h3>
            <p class="text-cyan-100">{{ t('docs.aiSupportAvailable') }}</p>
          </div>
          <div class="mt-4 md:mt-0 flex space-x-4">
            <a
              href="mailto:support@datamigrate.ai"
              class="px-6 py-3 bg-white text-cyan-600 rounded-lg font-semibold hover:bg-cyan-50 transition-colors"
            >
              {{ t('docs.contactSupport') }}
            </a>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* Doc card styles */
.doc-card {
  position: relative;
}

.doc-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 0.75rem;
  padding: 1px;
  background: linear-gradient(135deg, transparent 0%, rgba(6, 182, 212, 0.1) 100%);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
</style>
