<script setup lang="ts">
import { ref } from 'vue'

const searchQuery = ref('')

const docSections = [
  {
    title: 'Getting Started',
    description: 'Learn how to set up and configure DataMigrate AI for your first migration.',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-white to-cyan-50',
    topics: ['Quick Start Guide', 'Installation', 'First Migration', 'Configuration']
  },
  {
    title: 'Database Connections',
    description: 'Configure and manage your MSSQL database connections securely.',
    icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
    gradient: 'from-green-500 to-emerald-600',
    bgGradient: 'from-white to-green-50',
    topics: ['Connection Setup', 'Windows Auth', 'Connection Testing', 'Security']
  },
  {
    title: 'Migration Guide',
    description: 'Step-by-step guide to migrating your MSSQL databases to dbt projects.',
    icon: 'M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4',
    gradient: 'from-blue-500 to-cyan-600',
    bgGradient: 'from-white to-blue-50',
    topics: ['Table Selection', 'Schema Mapping', 'Data Types', 'Relationships']
  },
  {
    title: 'API Reference',
    description: 'Complete API documentation for integrating with DataMigrate AI.',
    icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
    gradient: 'from-slate-500 to-slate-700',
    bgGradient: 'from-white to-slate-50',
    topics: ['Authentication', 'Endpoints', 'Rate Limits', 'Webhooks']
  },
  {
    title: 'Best Practices',
    description: 'Guidelines for optimizing your data migrations and dbt projects.',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    gradient: 'from-amber-500 to-orange-600',
    bgGradient: 'from-white to-amber-50',
    topics: ['Performance', 'Error Handling', 'Testing', 'Deployment']
  },
  {
    title: 'Troubleshooting',
    description: 'Common issues and solutions for DataMigrate AI.',
    icon: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    gradient: 'from-red-500 to-rose-600',
    bgGradient: 'from-white to-red-50',
    topics: ['Connection Issues', 'Migration Errors', 'Performance', 'FAQs']
  }
]
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-cyan-50">
    <!-- Header -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-8">
          <h1 class="text-3xl font-bold text-white">Documentation</h1>
          <p class="mt-2 text-slate-300">
            Everything you need to know about DataMigrate AI
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
            placeholder="Search documentation..."
            class="block w-full pl-12 pr-4 py-4 border border-gray-200 rounded-2xl leading-5 bg-white placeholder-gray-400 shadow-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-base transition-all duration-200"
          />
        </div>
      </div>

      <!-- Documentation Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="section in docSections"
          :key="section.title"
          :class="[
            'doc-card overflow-hidden shadow-md rounded-xl border border-gray-100 hover:shadow-xl hover:scale-[1.02] transition-all duration-300 cursor-pointer group',
            `bg-gradient-to-br ${section.bgGradient}`
          ]"
        >
          <div class="p-6">
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
            </div>

            <!-- Topics -->
            <div class="mt-4 flex flex-wrap gap-2">
              <span
                v-for="topic in section.topics"
                :key="topic"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 hover:bg-cyan-100 hover:text-cyan-700 transition-colors cursor-pointer"
              >
                {{ topic }}
              </span>
            </div>

            <!-- Read More Link -->
            <div class="mt-4 pt-4 border-t border-gray-100">
              <button class="inline-flex items-center text-sm font-semibold text-cyan-600 hover:text-cyan-800 transition-colors">
                Read Documentation
                <svg class="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>
          <div :class="[
            'h-1 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left',
            `bg-gradient-to-r ${section.gradient}`
          ]"></div>
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
