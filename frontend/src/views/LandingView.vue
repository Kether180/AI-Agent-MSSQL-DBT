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
          <a href="#features" class="text-slate-300 hover:text-white transition-colors">Features</a>
          <a href="#how-it-works" class="text-slate-300 hover:text-white transition-colors">How It Works</a>
          <a href="#security" class="text-slate-300 hover:text-white transition-colors">Security</a>
          <router-link to="/login" class="text-slate-300 hover:text-white transition-colors">Sign In</router-link>
          <router-link
            to="/register"
            class="px-5 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-lg font-medium text-white transition-all transform hover:scale-105 shadow-lg shadow-purple-500/25"
          >
            Get Started Free
          </router-link>
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
        <div class="inline-flex items-center px-4 py-2 rounded-full bg-slate-800/50 border border-slate-700/50 mb-8 backdrop-blur-sm">
          <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></span>
          <span class="text-slate-300 text-sm">Powered by Claude AI</span>
        </div>

        <h1 class="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          <span class="text-white">Database Migrations</span><br>
          <span class="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Reimagined with AI
          </span>
        </h1>

        <p class="text-xl md:text-2xl text-slate-400 max-w-3xl mx-auto mb-12 leading-relaxed">
          Transform your legacy databases to modern data warehouses with AI-powered schema mapping,
          automated DBT transformations, and intelligent data quality analysis.
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
          <router-link
            to="/register"
            class="group px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-xl font-semibold text-lg text-white transition-all transform hover:scale-105 shadow-2xl shadow-purple-500/30 flex items-center space-x-2"
          >
            <span>Start Free Trial</span>
            <svg class="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </router-link>
          <router-link
            to="/login"
            class="px-8 py-4 bg-slate-800/50 hover:bg-slate-700/50 border border-slate-600 hover:border-slate-500 rounded-xl font-semibold text-lg text-white transition-all backdrop-blur-sm"
          >
            View Demo
          </router-link>
        </div>

        <!-- Floating Stats -->
        <div class="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6">
          <div class="p-4 bg-slate-800/30 rounded-xl border border-slate-700/50 backdrop-blur-sm">
            <div class="text-3xl font-bold text-white">10x</div>
            <div class="text-slate-400 text-sm">Faster Migrations</div>
          </div>
          <div class="p-4 bg-slate-800/30 rounded-xl border border-slate-700/50 backdrop-blur-sm">
            <div class="text-3xl font-bold text-white">99.9%</div>
            <div class="text-slate-400 text-sm">Data Accuracy</div>
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

    <!-- Features Section -->
    <section id="features" class="py-24 bg-slate-900 relative">
      <div class="max-w-7xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-4xl md:text-5xl font-bold text-white mb-4">
            Enterprise-Grade Features
          </h2>
          <p class="text-xl text-slate-400 max-w-2xl mx-auto">
            Everything you need to migrate, transform, and manage your data at scale
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
            <h3 class="text-xl font-semibold text-white mb-3">AI Schema Mapping</h3>
            <p class="text-slate-400">Intelligent analysis of source schemas with automatic mapping recommendations to target data warehouses.</p>
          </div>

          <!-- Feature 2 -->
          <div class="group p-8 bg-gradient-to-br from-slate-800/50 to-slate-800/30 rounded-2xl border border-slate-700/50 hover:border-purple-500/50 transition-all duration-300 hover:-translate-y-1">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">Auto DBT Generation</h3>
            <p class="text-slate-400">Automatically generate production-ready DBT models, tests, and documentation from your source data.</p>
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
            <h3 class="text-xl font-semibold text-white mb-3">Real-time Sync</h3>
            <p class="text-slate-400">CDC-based incremental migrations with near real-time data synchronization capabilities.</p>
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

    <!-- How It Works Section -->
    <section id="how-it-works" class="py-24 bg-gradient-to-b from-slate-900 to-slate-800 relative">
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
              Enterprise Security<br>
              <span class="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Built-In</span>
            </h2>
            <p class="text-xl text-slate-400 mb-8">
              Your data security is our top priority. We implement industry-leading security measures to protect your sensitive information.
            </p>

            <div class="space-y-4">
              <div class="flex items-start space-x-4">
                <div class="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h4 class="text-lg font-semibold text-white">End-to-End Encryption</h4>
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
                  <h4 class="text-lg font-semibold text-white">SOC 2 Type II Compliant</h4>
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
                  <h4 class="text-lg font-semibold text-white">GDPR & CCPA Ready</h4>
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
                  <h4 class="text-lg font-semibold text-white">Role-Based Access Control</h4>
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
          Ready to Transform Your<br>
          <span class="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Data Infrastructure?
          </span>
        </h2>
        <p class="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
          Join thousands of data engineers who trust DataMigrate AI for their mission-critical migrations.
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
          <router-link
            to="/register"
            class="group px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-xl font-semibold text-lg text-white transition-all transform hover:scale-105 shadow-2xl shadow-purple-500/30 flex items-center space-x-2"
          >
            <span>Start Free - No Credit Card</span>
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
            <p class="text-slate-400 text-sm">
              AI-powered database migrations for the modern data stack.
            </p>
          </div>

          <div>
            <h4 class="text-white font-semibold mb-4">Product</h4>
            <ul class="space-y-2 text-slate-400 text-sm">
              <li><a href="#features" class="hover:text-white transition-colors">Features</a></li>
              <li><a href="#security" class="hover:text-white transition-colors">Security</a></li>
              <li><router-link to="/docs" class="hover:text-white transition-colors">Documentation</router-link></li>
            </ul>
          </div>

          <div>
            <h4 class="text-white font-semibold mb-4">Company</h4>
            <ul class="space-y-2 text-slate-400 text-sm">
              <li><a href="#" class="hover:text-white transition-colors">About</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Blog</a></li>
              <li><a href="mailto:contact@datamigrate.ai" class="hover:text-white transition-colors">Contact</a></li>
            </ul>
          </div>

          <div>
            <h4 class="text-white font-semibold mb-4">Legal</h4>
            <ul class="space-y-2 text-slate-400 text-sm">
              <li><a href="#" class="hover:text-white transition-colors">Privacy Policy</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Terms of Service</a></li>
              <li><a href="#" class="hover:text-white transition-colors">GDPR</a></li>
            </ul>
          </div>
        </div>

        <div class="pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center">
          <p class="text-slate-500 text-sm">
            &copy; 2024 DataMigrate AI. All rights reserved.
          </p>
          <div class="flex space-x-6 mt-4 md:mt-0">
            <a href="#" class="text-slate-500 hover:text-white transition-colors">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/></svg>
            </a>
            <a href="#" class="text-slate-500 hover:text-white transition-colors">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            </a>
            <a href="#" class="text-slate-500 hover:text-white transition-colors">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
// Landing page component - no reactive state needed for static content
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
</style>
