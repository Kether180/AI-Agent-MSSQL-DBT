<template>
  <div class="landing-page">
    <!-- Navigation -->
    <nav class="fixed top-0 left-0 right-0 z-50 px-6 py-4 backdrop-blur-md bg-slate-900/80 border-b border-slate-700/50">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          </div>
          <span class="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            DataMigrate AI
          </span>
        </div>
        <div class="hidden md:flex items-center space-x-8">
          <a href="#features" class="text-slate-300 hover:text-white transition-colors">{{ $t('nav.features') }}</a>
          <a href="#agents" class="text-slate-300 hover:text-white transition-colors">{{ $t('nav.agents') }}</a>
          <a href="#benefits" class="text-slate-300 hover:text-white transition-colors">{{ $t('nav.benefits') }}</a>
          <a href="#security" class="text-slate-300 hover:text-white transition-colors">{{ $t('nav.security') }}</a>
          <LanguageSelector />
          <router-link to="/login" class="text-slate-300 hover:text-white transition-colors">{{ $t('nav.login') }}</router-link>
          <router-link
            to="/register"
            class="px-5 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-lg font-medium text-white transition-all transform hover:scale-105 shadow-lg shadow-purple-500/25"
          >
            {{ $t('nav.getStarted') }}
          </router-link>
        </div>
        <!-- Mobile menu with language selector -->
        <div class="md:hidden flex items-center space-x-3">
          <LanguageSelector />
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="min-h-screen flex items-center justify-center relative overflow-hidden pt-20">
      <!-- Animated Background -->
      <div class="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900"></div>
      <div class="absolute inset-0">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full filter blur-3xl animate-pulse"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full filter blur-3xl animate-pulse delay-1000"></div>
        <div class="absolute top-1/2 left-1/2 w-64 h-64 bg-cyan-500/10 rounded-full filter blur-3xl animate-pulse delay-500"></div>
      </div>

      <!-- Grid Pattern -->
      <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0wIDBoNjB2NjBIMHoiLz48cGF0aCBkPSJNMzAgMzBtLTEgMGExIDEgMCAxIDAgMiAwYTEgMSAwIDEgMCAtMiAwIiBmaWxsPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMSkiLz48L2c+PC9zdmc+')] opacity-40"></div>

      <div class="relative z-10 max-w-5xl mx-auto px-6 text-center">
        <!-- Animated Logo -->
        <div class="mb-8 flex justify-center">
          <div class="relative">
            <div class="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-2xl shadow-purple-500/40 animate-float">
              <svg class="w-12 h-12 md:w-14 md:h-14 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
              </svg>
            </div>
            <!-- Glow rings -->
            <div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 blur-xl opacity-40 animate-pulse"></div>
          </div>
        </div>

        <div class="inline-flex items-center px-4 py-2 rounded-full bg-slate-800/50 border border-slate-700/50 mb-8 backdrop-blur-sm">
          <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></span>
          <span class="text-slate-300 text-sm">{{ $t('hero.badge') }}</span>
        </div>

        <h1 class="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          <span class="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            {{ $t('hero.title1') }}
          </span>
          <span class="text-white"> {{ $t('hero.title2') }}</span><br>
          <span class="text-white">{{ $t('hero.title3') }} </span>
          <span class="bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            {{ $t('hero.title4') }}
          </span>
        </h1>

        <p class="text-xl md:text-2xl text-slate-400 max-w-3xl mx-auto mb-12 leading-relaxed">
          {{ $t('hero.subtitle') }}
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
          <router-link
            to="/register"
            class="group px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-xl font-semibold text-lg text-white transition-all transform hover:scale-105 shadow-2xl shadow-purple-500/30 flex items-center space-x-2"
          >
            <span>{{ $t('hero.cta') }}</span>
            <svg class="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </router-link>
          <router-link
            to="/login"
            class="px-8 py-4 bg-slate-800/50 hover:bg-slate-700/50 border border-slate-600 hover:border-slate-500 rounded-xl font-semibold text-lg text-white transition-all backdrop-blur-sm"
          >
            {{ $t('hero.demo') }}
          </router-link>
        </div>

        <!-- Floating Stats - Fixed spacing with mb-16 -->
        <div class="mt-20 mb-16 grid grid-cols-2 md:grid-cols-4 gap-6">
          <div class="p-4 bg-slate-800/30 rounded-xl border border-slate-700/50 backdrop-blur-sm">
            <div class="text-3xl font-bold text-white">10x</div>
            <div class="text-slate-400 text-sm">{{ $t('hero.stats.faster') }}</div>
          </div>
          <div class="p-4 bg-slate-800/30 rounded-xl border border-slate-700/50 backdrop-blur-sm">
            <div class="text-3xl font-bold text-white">99.9%</div>
            <div class="text-slate-400 text-sm">{{ $t('benefits.items.errors.title').split(' ').slice(-1)[0] || 'Accuracy' }}</div>
          </div>
          <div class="p-4 bg-slate-800/30 rounded-xl border border-slate-700/50 backdrop-blur-sm">
            <div class="text-3xl font-bold text-white">50+</div>
            <div class="text-slate-400 text-sm">Database Types</div>
          </div>
          <div class="p-4 bg-slate-800/30 rounded-xl border border-slate-700/50 backdrop-blur-sm">
            <div class="text-3xl font-bold text-white">24/7</div>
            <div class="text-slate-400 text-sm">AI Assistance</div>
          </div>
        </div>
      </div>

      <!-- Scroll Indicator -->
      <div class="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <svg class="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>

    <!-- Benefits Section - NEW -->
    <section id="benefits" class="py-24 bg-gradient-to-b from-slate-900 via-slate-800/80 to-slate-900 relative overflow-hidden">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-1/4 right-1/4 w-96 h-96 bg-emerald-500/30 rounded-full filter blur-3xl"></div>
        <div class="absolute bottom-1/4 left-1/4 w-96 h-96 bg-blue-500/30 rounded-full filter blur-3xl"></div>
      </div>

      <div class="max-w-7xl mx-auto px-6 relative z-10">
        <div class="text-center mb-16">
          <div class="inline-flex items-center px-4 py-2 rounded-full bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border border-emerald-500/30 mb-6">
            <svg class="w-5 h-5 text-emerald-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <span class="text-emerald-300 text-sm font-medium">ROI & Business Impact</span>
          </div>
          <h2 class="text-4xl md:text-5xl font-bold text-white mb-4">
            {{ $t('benefits.title') }}
          </h2>
          <p class="text-xl text-slate-400 max-w-2xl mx-auto">
            {{ $t('benefits.subtitle') }}
          </p>
        </div>

        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <!-- Benefit 1: Cost Reduction -->
          <div class="group p-8 bg-gradient-to-br from-emerald-900/40 to-slate-800/40 rounded-2xl border border-emerald-500/30 hover:border-emerald-400/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-2xl font-bold text-white mb-3">{{ $t('benefits.items.cost.title') }}</h3>
            <p class="text-slate-400">{{ $t('benefits.items.cost.description') }}</p>
          </div>

          <!-- Benefit 2: Time Savings -->
          <div class="group p-8 bg-gradient-to-br from-blue-900/40 to-slate-800/40 rounded-2xl border border-blue-500/30 hover:border-blue-400/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-2xl font-bold text-white mb-3">{{ $t('benefits.items.time.title') }}</h3>
            <p class="text-slate-400">{{ $t('benefits.items.time.description') }}</p>
          </div>

          <!-- Benefit 3: Accuracy -->
          <div class="group p-8 bg-gradient-to-br from-purple-900/40 to-slate-800/40 rounded-2xl border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-2xl font-bold text-white mb-3">{{ $t('benefits.items.errors.title') }}</h3>
            <p class="text-slate-400">{{ $t('benefits.items.errors.description') }}</p>
          </div>

          <!-- Benefit 4: Zero Downtime -->
          <div class="group p-8 bg-gradient-to-br from-cyan-900/40 to-slate-800/40 rounded-2xl border border-cyan-500/30 hover:border-cyan-400/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <h3 class="text-2xl font-bold text-white mb-3">{{ $t('benefits.items.downtime.title') }}</h3>
            <p class="text-slate-400">{{ $t('benefits.items.downtime.description') }}</p>
          </div>

          <!-- Benefit 5: No Expertise Required -->
          <div class="group p-8 bg-gradient-to-br from-orange-900/40 to-slate-800/40 rounded-2xl border border-orange-500/30 hover:border-orange-400/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 class="text-2xl font-bold text-white mb-3">{{ $t('benefits.items.expertise.title') }}</h3>
            <p class="text-slate-400">{{ $t('benefits.items.expertise.description') }}</p>
          </div>

          <!-- Benefit 6: Scalable -->
          <div class="group p-8 bg-gradient-to-br from-pink-900/40 to-slate-800/40 rounded-2xl border border-pink-500/30 hover:border-pink-400/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-pink-500 to-pink-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <h3 class="text-2xl font-bold text-white mb-3">{{ $t('benefits.items.scalable.title') }}</h3>
            <p class="text-slate-400">{{ $t('benefits.items.scalable.description') }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Integrations / Data Warehouses Section -->
    <section class="py-24 bg-gradient-to-b from-slate-900 via-slate-800/50 to-slate-900 relative overflow-hidden">
      <!-- Background decorations -->
      <div class="absolute inset-0 opacity-30">
        <div class="absolute top-0 left-1/4 w-64 h-64 bg-blue-500/20 rounded-full filter blur-3xl"></div>
        <div class="absolute bottom-0 right-1/4 w-64 h-64 bg-purple-500/20 rounded-full filter blur-3xl"></div>
      </div>

      <div class="max-w-7xl mx-auto px-6 relative z-10">
        <!-- Section Header -->
        <div class="text-center mb-12">
          <div class="inline-flex items-center px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/30 mb-4">
            <svg class="w-4 h-4 text-blue-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span class="text-blue-300 text-sm font-medium">{{ $t('integrations.title') }}</span>
          </div>
          <h2 class="text-3xl md:text-4xl font-bold text-white mb-3">
            Connect to <span class="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Any Platform</span>
          </h2>
          <p class="text-slate-400 max-w-2xl mx-auto">
            {{ $t('integrations.subtitle') }}
          </p>
        </div>

        <!-- Target Data Warehouses -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-16">
          <!-- Snowflake -->
          <div class="group relative">
            <div class="p-4 bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 hover:border-blue-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:-translate-y-1">
              <div class="flex flex-col items-center">
                <div class="w-14 h-14 mb-3 rounded-xl bg-gradient-to-br from-blue-400/20 to-blue-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="text-3xl">&#10052;&#65039;</span>
                </div>
                <span class="text-white text-sm font-semibold">Snowflake</span>
                <span class="text-blue-400 text-xs mt-1">Cloud DW</span>
              </div>
            </div>
          </div>

          <!-- Google BigQuery -->
          <div class="group relative">
            <div class="p-4 bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 hover:border-yellow-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-yellow-500/10 hover:-translate-y-1">
              <div class="flex flex-col items-center">
                <div class="w-14 h-14 mb-3 rounded-xl bg-gradient-to-br from-yellow-400/20 to-blue-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="text-3xl">&#128311;</span>
                </div>
                <span class="text-white text-sm font-semibold">BigQuery</span>
                <span class="text-yellow-400 text-xs mt-1">Google Cloud</span>
              </div>
            </div>
          </div>

          <!-- Databricks -->
          <div class="group relative">
            <div class="p-4 bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 hover:border-red-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-red-500/10 hover:-translate-y-1">
              <div class="flex flex-col items-center">
                <div class="w-14 h-14 mb-3 rounded-xl bg-gradient-to-br from-red-400/20 to-orange-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="text-3xl">&#129521;</span>
                </div>
                <span class="text-white text-sm font-semibold">Databricks</span>
                <span class="text-red-400 text-xs mt-1">Lakehouse</span>
              </div>
            </div>
          </div>

          <!-- Amazon Redshift -->
          <div class="group relative">
            <div class="p-4 bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 hover:border-orange-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/10 hover:-translate-y-1">
              <div class="flex flex-col items-center">
                <div class="w-14 h-14 mb-3 rounded-xl bg-gradient-to-br from-orange-400/20 to-red-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="text-3xl">&#128310;</span>
                </div>
                <span class="text-white text-sm font-semibold">Redshift</span>
                <span class="text-orange-400 text-xs mt-1">AWS</span>
              </div>
            </div>
          </div>

          <!-- Azure Synapse -->
          <div class="group relative">
            <div class="p-4 bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 hover:border-cyan-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10 hover:-translate-y-1">
              <div class="flex flex-col items-center">
                <div class="w-14 h-14 mb-3 rounded-xl bg-gradient-to-br from-cyan-400/20 to-blue-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="text-3xl">&#128313;</span>
                </div>
                <span class="text-white text-sm font-semibold">Synapse</span>
                <span class="text-cyan-400 text-xs mt-1">Azure</span>
              </div>
            </div>
          </div>

          <!-- dbt -->
          <div class="group relative">
            <div class="p-4 bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 hover:border-orange-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/10 hover:-translate-y-1">
              <div class="flex flex-col items-center">
                <div class="w-14 h-14 mb-3 rounded-xl bg-gradient-to-br from-orange-400/20 to-orange-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="text-3xl">&#9889;</span>
                </div>
                <span class="text-white text-sm font-semibold">dbt</span>
                <span class="text-orange-500 text-xs mt-1">Transform</span>
              </div>
            </div>
          </div>

          <!-- Apache Spark -->
          <div class="group relative">
            <div class="p-4 bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 hover:border-orange-600/50 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/10 hover:-translate-y-1">
              <div class="flex flex-col items-center">
                <div class="w-14 h-14 mb-3 rounded-xl bg-gradient-to-br from-orange-500/20 to-yellow-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="text-3xl">&#128293;</span>
                </div>
                <span class="text-white text-sm font-semibold">Spark</span>
                <span class="text-orange-600 text-xs mt-1">Apache</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Animated Connection Line -->
        <div class="flex items-center justify-center mb-12">
          <div class="flex-1 h-px bg-gradient-to-r from-transparent via-slate-600 to-transparent"></div>
          <div class="px-6 py-3 bg-slate-800/80 rounded-full border border-slate-700/50 mx-4">
            <div class="flex items-center space-x-3">
              <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span class="text-slate-300 text-sm font-medium">{{ $t('integrations.pipeline') }}</span>
              <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>
          </div>
          <div class="flex-1 h-px bg-gradient-to-r from-transparent via-slate-600 to-transparent"></div>
        </div>

        <!-- Source Databases -->
        <div class="text-center mb-8">
          <h3 class="text-xl font-semibold text-white mb-2">{{ $t('integrations.source') }}</h3>
          <p class="text-slate-500 text-sm">Connect to your existing databases with secure, read-only access</p>
        </div>

        <div class="flex flex-wrap justify-center gap-3">
          <div class="group px-5 py-3 bg-gradient-to-r from-blue-900/40 to-slate-800/40 rounded-xl border border-blue-500/30 hover:border-blue-400/50 transition-all hover:shadow-lg hover:shadow-blue-500/10">
            <div class="flex items-center space-x-2">
              <span class="text-xl">&#128452;&#65039;</span>
              <span class="text-white font-medium">MSSQL Server</span>
            </div>
          </div>
          <div class="group px-5 py-3 bg-gradient-to-r from-blue-900/40 to-slate-800/40 rounded-xl border border-blue-500/30 hover:border-blue-400/50 transition-all hover:shadow-lg hover:shadow-blue-500/10">
            <div class="flex items-center space-x-2">
              <span class="text-xl">&#128024;</span>
              <span class="text-white font-medium">PostgreSQL</span>
            </div>
          </div>
          <div class="group px-5 py-3 bg-gradient-to-r from-orange-900/40 to-slate-800/40 rounded-xl border border-orange-500/30 hover:border-orange-400/50 transition-all hover:shadow-lg hover:shadow-orange-500/10">
            <div class="flex items-center space-x-2">
              <span class="text-xl">&#128044;</span>
              <span class="text-white font-medium">MySQL</span>
            </div>
          </div>
          <div class="group px-5 py-3 bg-gradient-to-r from-red-900/40 to-slate-800/40 rounded-xl border border-red-500/30 hover:border-red-400/50 transition-all hover:shadow-lg hover:shadow-red-500/10">
            <div class="flex items-center space-x-2">
              <span class="text-xl">&#128308;</span>
              <span class="text-white font-medium">Oracle</span>
            </div>
          </div>
          <div class="group px-5 py-3 bg-gradient-to-r from-purple-900/40 to-slate-800/40 rounded-xl border border-purple-500/30 hover:border-purple-400/50 transition-all hover:shadow-lg hover:shadow-purple-500/10">
            <div class="flex items-center space-x-2">
              <span class="text-xl">&#128190;</span>
              <span class="text-white font-medium">IBM DB2</span>
            </div>
          </div>
          <div class="group px-5 py-3 bg-gradient-to-r from-green-900/40 to-slate-800/40 rounded-xl border border-green-500/30 hover:border-green-400/50 transition-all hover:shadow-lg hover:shadow-green-500/10">
            <div class="flex items-center space-x-2">
              <span class="text-xl">&#127811;</span>
              <span class="text-white font-medium">MongoDB</span>
            </div>
          </div>
          <div class="group px-5 py-3 bg-gradient-to-r from-cyan-900/40 to-slate-800/40 rounded-xl border border-cyan-500/30 hover:border-cyan-400/50 transition-all hover:shadow-lg hover:shadow-cyan-500/10">
            <div class="flex items-center space-x-2">
              <span class="text-xl">&#128202;</span>
              <span class="text-white font-medium">SAP HANA</span>
            </div>
          </div>
          <div class="group px-5 py-3 bg-gradient-to-r from-slate-700/40 to-slate-800/40 rounded-xl border border-slate-500/30 hover:border-slate-400/50 transition-all hover:shadow-lg hover:shadow-slate-500/10">
            <div class="flex items-center space-x-2">
              <span class="text-xl">&#128193;</span>
              <span class="text-white font-medium">CSV / Excel</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="py-24 bg-slate-900 relative">
      <div class="max-w-7xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-4xl md:text-5xl font-bold text-white mb-4">
            {{ $t('features.title') }}
          </h2>
          <p class="text-xl text-slate-400 max-w-2xl mx-auto">
            {{ $t('features.subtitle') }}
          </p>
        </div>

        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <!-- Feature 1 -->
          <div class="group p-8 bg-gradient-to-br from-slate-800/50 to-slate-800/30 rounded-2xl border border-slate-700/50 hover:border-blue-500/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">{{ $t('features.items.schema.title') }}</h3>
            <p class="text-slate-400">{{ $t('features.items.schema.description') }}</p>
          </div>

          <!-- Feature 2 -->
          <div class="group p-8 bg-gradient-to-br from-slate-800/50 to-slate-800/30 rounded-2xl border border-slate-700/50 hover:border-purple-500/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">{{ $t('features.items.dbt.title') }}</h3>
            <p class="text-slate-400">{{ $t('features.items.dbt.description') }}</p>
          </div>

          <!-- Feature 3 -->
          <div class="group p-8 bg-gradient-to-br from-slate-800/50 to-slate-800/30 rounded-2xl border border-slate-700/50 hover:border-cyan-500/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">Data Quality AI</h3>
            <p class="text-slate-400">ML-powered data quality checks that detect anomalies, validate patterns, and ensure data integrity.</p>
          </div>

          <!-- Feature 4 -->
          <div class="group p-8 bg-gradient-to-br from-slate-800/50 to-slate-800/30 rounded-2xl border border-slate-700/50 hover:border-green-500/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">Multi-Warehouse Support</h3>
            <p class="text-slate-400">Migrate to Snowflake, BigQuery, Databricks, Redshift, and more with native connectors.</p>
          </div>

          <!-- Feature 5 -->
          <div class="group p-8 bg-gradient-to-br from-slate-800/50 to-slate-800/30 rounded-2xl border border-slate-700/50 hover:border-orange-500/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">{{ $t('features.items.realtime.title') }}</h3>
            <p class="text-slate-400">{{ $t('features.items.realtime.description') }}</p>
          </div>

          <!-- Feature 6 -->
          <div class="group p-8 bg-gradient-to-br from-slate-800/50 to-slate-800/30 rounded-2xl border border-slate-700/50 hover:border-pink-500/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-pink-500 to-pink-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">BI Integration</h3>
            <p class="text-slate-400">Connect your BI tools directly and get AI-assisted query optimization for better insights.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- AI Agents Section -->
    <section id="agents" class="py-24 bg-gradient-to-b from-slate-900 to-slate-800 relative overflow-hidden">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-1/3 left-1/4 w-72 h-72 bg-cyan-500/30 rounded-full filter blur-3xl animate-pulse"></div>
        <div class="absolute bottom-1/3 right-1/4 w-72 h-72 bg-purple-500/30 rounded-full filter blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div class="max-w-7xl mx-auto px-6 relative z-10">
        <div class="text-center mb-16">
          <div class="inline-flex items-center px-4 py-2 rounded-full bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 mb-6">
            <svg class="w-5 h-5 text-cyan-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span class="text-cyan-300 text-sm font-medium">Autonomous AI Agents</span>
          </div>
          <h2 class="text-4xl md:text-5xl font-bold text-white mb-4">
            {{ $t('agents.title') }}
          </h2>
          <p class="text-xl text-slate-400 max-w-2xl mx-auto">
            {{ $t('agents.subtitle') }}
          </p>
        </div>

        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Agent 1: MSSQL Extractor -->
          <div class="group p-6 bg-gradient-to-br from-blue-900/40 to-slate-800/40 rounded-2xl border border-blue-500/30 hover:border-blue-400/50 transition-all duration-300">
            <div class="flex items-center space-x-4 mb-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('agents.items.extractor.title') }}</h3>
                <span class="text-xs text-blue-400 font-medium">Schema Analysis</span>
              </div>
            </div>
            <p class="text-slate-400 text-sm">{{ $t('agents.items.extractor.description') }}</p>
          </div>

          <!-- Agent 2: Data Prep Agent -->
          <div class="group p-6 bg-gradient-to-br from-purple-900/40 to-slate-800/40 rounded-2xl border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
            <div class="flex items-center space-x-4 mb-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('agents.items.dataprep.title') }}</h3>
                <span class="text-xs text-purple-400 font-medium">Transformation</span>
              </div>
            </div>
            <p class="text-slate-400 text-sm">{{ $t('agents.items.dataprep.description') }}</p>
          </div>

          <!-- Agent 3: DBT Generator Agent -->
          <div class="group p-6 bg-gradient-to-br from-orange-900/40 to-slate-800/40 rounded-2xl border border-orange-500/30 hover:border-orange-400/50 transition-all duration-300">
            <div class="flex items-center space-x-4 mb-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('agents.items.dbt.title') }}</h3>
                <span class="text-xs text-orange-400 font-medium">Code Generation</span>
              </div>
            </div>
            <p class="text-slate-400 text-sm">{{ $t('agents.items.dbt.description') }}</p>
          </div>

          <!-- Agent 4: Data Quality Agent -->
          <div class="group p-6 bg-gradient-to-br from-green-900/40 to-slate-800/40 rounded-2xl border border-green-500/30 hover:border-green-400/50 transition-all duration-300">
            <div class="flex items-center space-x-4 mb-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('agents.items.quality.title') }}</h3>
                <span class="text-xs text-green-400 font-medium">Validation</span>
              </div>
            </div>
            <p class="text-slate-400 text-sm">{{ $t('agents.items.quality.description') }}</p>
          </div>

          <!-- Agent 5: Documentation Agent -->
          <div class="group p-6 bg-gradient-to-br from-cyan-900/40 to-slate-800/40 rounded-2xl border border-cyan-500/30 hover:border-cyan-400/50 transition-all duration-300">
            <div class="flex items-center space-x-4 mb-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('agents.items.docs.title') }}</h3>
                <span class="text-xs text-cyan-400 font-medium">Auto-Docs</span>
              </div>
            </div>
            <p class="text-slate-400 text-sm">{{ $t('agents.items.docs.description') }}</p>
          </div>

          <!-- Agent 6: RAG Service Agent -->
          <div class="group p-6 bg-gradient-to-br from-pink-900/40 to-slate-800/40 rounded-2xl border border-pink-500/30 hover:border-pink-400/50 transition-all duration-300">
            <div class="flex items-center space-x-4 mb-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-pink-600 flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('agents.items.rag.title') }}</h3>
                <span class="text-xs text-pink-400 font-medium">Learning</span>
              </div>
            </div>
            <p class="text-slate-400 text-sm">{{ $t('agents.items.rag.description') }}</p>
          </div>

          <!-- Agent 7: BI Analytics Agent -->
          <div class="group p-6 bg-gradient-to-br from-indigo-900/40 to-slate-800/40 rounded-2xl border border-indigo-500/30 hover:border-indigo-400/50 transition-all duration-300">
            <div class="flex items-center space-x-4 mb-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('agents.items.bi.title') }}</h3>
                <span class="text-xs text-indigo-400 font-medium">Insights</span>
              </div>
            </div>
            <p class="text-slate-400 text-sm">{{ $t('agents.items.bi.description') }}</p>
          </div>

          <!-- Agent 8: Validation Agent -->
          <div class="group p-6 bg-gradient-to-br from-amber-900/40 to-slate-800/40 rounded-2xl border border-amber-500/30 hover:border-amber-400/50 transition-all duration-300">
            <div class="flex items-center space-x-4 mb-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('agents.items.validation.title') }}</h3>
                <span class="text-xs text-amber-400 font-medium">Testing</span>
              </div>
            </div>
            <p class="text-slate-400 text-sm">{{ $t('agents.items.validation.description') }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How It Works Section -->
    <section id="how-it-works" class="py-24 bg-slate-800 relative">
      <div class="max-w-7xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-4xl md:text-5xl font-bold text-white mb-4">
            How It Works
          </h2>
          <p class="text-xl text-slate-400 max-w-2xl mx-auto">
            Four simple steps to modernize your data infrastructure
          </p>
        </div>

        <div class="grid md:grid-cols-4 gap-8">
          <!-- Step 1 -->
          <div class="text-center relative">
            <div class="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white mb-6 shadow-lg shadow-purple-500/30">
              1
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">Connect Source</h3>
            <p class="text-slate-400">Connect your MSSQL, PostgreSQL, MySQL, or Oracle database securely.</p>
            <div class="hidden md:block absolute top-8 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-purple-500 to-transparent"></div>
          </div>

          <!-- Step 2 -->
          <div class="text-center relative">
            <div class="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-2xl font-bold text-white mb-6 shadow-lg shadow-pink-500/30">
              2
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">AI Analysis</h3>
            <p class="text-slate-400">Our AI analyzes schema, data patterns, and suggests optimal transformations.</p>
            <div class="hidden md:block absolute top-8 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-pink-500 to-transparent"></div>
          </div>

          <!-- Step 3 -->
          <div class="text-center relative">
            <div class="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-pink-500 to-orange-600 flex items-center justify-center text-2xl font-bold text-white mb-6 shadow-lg shadow-orange-500/30">
              3
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">Generate DBT</h3>
            <p class="text-slate-400">Auto-generate DBT models, documentation, and tests for your pipeline.</p>
            <div class="hidden md:block absolute top-8 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-orange-500 to-transparent"></div>
          </div>

          <!-- Step 4 -->
          <div class="text-center">
            <div class="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-orange-500 to-green-600 flex items-center justify-center text-2xl font-bold text-white mb-6 shadow-lg shadow-green-500/30">
              4
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">Deploy & Monitor</h3>
            <p class="text-slate-400">Deploy to your warehouse with continuous monitoring and quality checks.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Security Section -->
    <section id="security" class="py-24 bg-slate-800 relative overflow-hidden">
      <div class="absolute inset-0 opacity-30">
        <div class="absolute top-0 right-0 w-96 h-96 bg-blue-500/20 rounded-full filter blur-3xl"></div>
        <div class="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/20 rounded-full filter blur-3xl"></div>
      </div>

      <div class="max-w-7xl mx-auto px-6 relative z-10">
        <div class="grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 class="text-4xl md:text-5xl font-bold text-white mb-6">
              {{ $t('security.title') }}<br>
              <span class="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Built-In</span>
            </h2>
            <p class="text-xl text-slate-400 mb-8">
              {{ $t('security.subtitle') }}
            </p>

            <div class="space-y-4">
              <div class="flex items-start space-x-4">
                <div class="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h4 class="text-lg font-semibold text-white">{{ $t('security.items.encryption') }}</h4>
                  <p class="text-slate-400">AES-256 encryption for data at rest and TLS 1.3 for data in transit.</p>
                </div>
              </div>

              <div class="flex items-start space-x-4">
                <div class="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h4 class="text-lg font-semibold text-white">{{ $t('security.items.soc2') }}</h4>
                  <p class="text-slate-400">Audited security controls with continuous monitoring and compliance.</p>
                </div>
              </div>

              <div class="flex items-start space-x-4">
                <div class="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h4 class="text-lg font-semibold text-white">{{ $t('security.items.gdpr') }}</h4>
                  <p class="text-slate-400">Built-in PII detection, data masking, and compliance reporting.</p>
                </div>
              </div>

              <div class="flex items-start space-x-4">
                <div class="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h4 class="text-lg font-semibold text-white">{{ $t('security.items.rbac') }}</h4>
                  <p class="text-slate-400">Granular permissions with SSO integration and audit logging.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Security Metrics Visual -->
          <div class="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-8 backdrop-blur-sm">
            <div class="text-center mb-8">
              <h3 class="text-2xl font-bold text-white mb-2">Security Score</h3>
              <div class="text-6xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
                A+
              </div>
            </div>

            <div class="space-y-4">
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-slate-400">Encryption</span>
                  <span class="text-green-400">100%</span>
                </div>
                <div class="h-2 bg-slate-700 rounded-full">
                  <div class="h-2 bg-gradient-to-r from-green-400 to-emerald-400 rounded-full" style="width: 100%"></div>
                </div>
              </div>

              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-slate-400">Access Control</span>
                  <span class="text-green-400">98%</span>
                </div>
                <div class="h-2 bg-slate-700 rounded-full">
                  <div class="h-2 bg-gradient-to-r from-green-400 to-emerald-400 rounded-full" style="width: 98%"></div>
                </div>
              </div>

              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-slate-400">Vulnerability Protection</span>
                  <span class="text-green-400">99%</span>
                </div>
                <div class="h-2 bg-slate-700 rounded-full">
                  <div class="h-2 bg-gradient-to-r from-green-400 to-emerald-400 rounded-full" style="width: 99%"></div>
                </div>
              </div>

              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-slate-400">Audit Logging</span>
                  <span class="text-green-400">100%</span>
                </div>
                <div class="h-2 bg-slate-700 rounded-full">
                  <div class="h-2 bg-gradient-to-r from-green-400 to-emerald-400 rounded-full" style="width: 100%"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="py-24 bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 relative">
      <div class="max-w-4xl mx-auto px-6 text-center">
        <h2 class="text-4xl md:text-5xl font-bold text-white mb-6">
          {{ $t('cta.title') }}<br>
          <span class="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Data Infrastructure?
          </span>
        </h2>
        <p class="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
          {{ $t('cta.subtitle') }}
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
          <router-link
            to="/register"
            class="group px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-xl font-semibold text-lg text-white transition-all transform hover:scale-105 shadow-2xl shadow-purple-500/30 flex items-center space-x-2"
          >
            <span>{{ $t('cta.button') }}</span>
            <svg class="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </router-link>
          <a
            href="mailto:contact@datamigrate.ai"
            class="px-8 py-4 text-slate-300 hover:text-white transition-colors font-medium"
          >
            Contact Sales
          </a>
        </div>
        <p class="text-slate-500 text-sm mt-4">{{ $t('cta.note') }}</p>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-slate-900 border-t border-slate-800 py-12">
      <div class="max-w-7xl mx-auto px-6">
        <div class="grid md:grid-cols-4 gap-8 mb-8">
          <div>
            <div class="flex items-center space-x-3 mb-4">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <span class="text-xl font-bold text-white">DataMigrate AI</span>
            </div>
            <p class="text-slate-400 text-sm mb-2">
              AI-powered database migrations for the modern data stack.
            </p>
            <p class="text-slate-500 text-xs">
              {{ $t('footer.madeBy') }} <span class="text-slate-400 font-medium">Okoinvestments ApS</span>
            </p>
          </div>

          <div>
            <h4 class="text-white font-semibold mb-4">{{ $t('footer.product') }}</h4>
            <ul class="space-y-2 text-slate-400 text-sm">
              <li><a href="#features" class="hover:text-white transition-colors">{{ $t('nav.features') }}</a></li>
              <li><a href="#agents" class="hover:text-white transition-colors">{{ $t('nav.agents') }}</a></li>
              <li><a href="#security" class="hover:text-white transition-colors">{{ $t('nav.security') }}</a></li>
              <li><router-link to="/docs" class="hover:text-white transition-colors">Documentation</router-link></li>
            </ul>
          </div>

          <div>
            <h4 class="text-white font-semibold mb-4">{{ $t('footer.company') }}</h4>
            <ul class="space-y-2 text-slate-400 text-sm">
              <li><a href="#" class="hover:text-white transition-colors">About Okoinvestments</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Blog</a></li>
              <li><a href="mailto:contact@okoinvestments.com" class="hover:text-white transition-colors">Contact</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Careers</a></li>
            </ul>
          </div>

          <div>
            <h4 class="text-white font-semibold mb-4">{{ $t('footer.legal') }}</h4>
            <ul class="space-y-2 text-slate-400 text-sm">
              <li><a href="#" class="hover:text-white transition-colors">Privacy Policy</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Terms of Service</a></li>
              <li><a href="#" class="hover:text-white transition-colors">GDPR</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Data Processing</a></li>
            </ul>
          </div>
        </div>

        <div class="pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center">
          <div class="text-center md:text-left mb-4 md:mb-0">
            <p class="text-slate-500 text-sm">
              &copy; 2025 DataMigrate AI. {{ $t('footer.copyright') }}
            </p>
            <p class="text-slate-600 text-xs mt-1">
              Okoinvestments ApS - Denmark
            </p>
          </div>
          <div class="flex space-x-5">
            <!-- LinkedIn -->
            <a href="https://linkedin.com/company/okoinvestments" target="_blank" rel="noopener noreferrer" class="text-slate-500 hover:text-blue-400 transition-colors" title="LinkedIn">
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
            </a>
            <!-- Instagram -->
            <a href="https://instagram.com/okoinvestments" target="_blank" rel="noopener noreferrer" class="text-slate-500 hover:text-pink-400 transition-colors" title="Instagram">
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
            </a>
            <!-- YouTube -->
            <a href="https://youtube.com/@okoinvestments" target="_blank" rel="noopener noreferrer" class="text-slate-500 hover:text-red-500 transition-colors" title="YouTube">
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            </a>
            <!-- GitHub -->
            <a href="https://github.com/okoinvestments" target="_blank" rel="noopener noreferrer" class="text-slate-500 hover:text-white transition-colors" title="GitHub">
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import LanguageSelector from '@/components/LanguageSelector.vue'
</script>

<style scoped>
.landing-page {
  background-color: #0f172a;
  color: white;
  min-height: 100vh;
}

/* Animation delays for pulse effects */
.delay-500 {
  animation-delay: 500ms;
}

.delay-1000 {
  animation-delay: 1000ms;
}

/* Floating animation for logo */
@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}
</style>
