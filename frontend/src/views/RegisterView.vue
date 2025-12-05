<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Form fields
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const organizationName = ref('')
const jobTitle = ref('')
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const isFormValid = computed(() => {
  return (
    firstName.value.length > 0 &&
    lastName.value.length > 0 &&
    email.value.length > 0 &&
    organizationName.value.length >= 2 &&
    password.value.length >= 6 &&
    password.value === confirmPassword.value
  )
})

const passwordsMatch = computed(() => {
  return confirmPassword.value.length === 0 || password.value === confirmPassword.value
})

// Password strength indicators
const passwordLength = computed(() => password.value.length >= 6)
const passwordHasNumber = computed(() => /\d/.test(password.value))
const passwordHasLetter = computed(() => /[a-zA-Z]/.test(password.value))
const passwordStrength = computed(() => {
  let strength = 0
  if (password.value.length >= 6) strength++
  if (password.value.length >= 8) strength++
  if (/\d/.test(password.value)) strength++
  if (/[a-zA-Z]/.test(password.value)) strength++
  if (/[^a-zA-Z0-9]/.test(password.value)) strength++
  return strength
})
const passwordStrengthLabel = computed(() => {
  if (password.value.length === 0) return ''
  if (passwordStrength.value <= 2) return 'Weak'
  if (passwordStrength.value <= 3) return 'Medium'
  if (passwordStrength.value <= 4) return 'Strong'
  return 'Very Strong'
})
const passwordStrengthColor = computed(() => {
  if (passwordStrength.value <= 2) return 'bg-gradient-to-r from-red-500 to-rose-500'
  if (passwordStrength.value <= 3) return 'bg-gradient-to-r from-amber-500 to-yellow-500'
  if (passwordStrength.value <= 4) return 'bg-gradient-to-r from-emerald-500 to-green-500'
  return 'bg-gradient-to-r from-emerald-500 to-teal-500'
})

const handleRegister = async () => {
  if (!isFormValid.value) {
    if (password.value !== confirmPassword.value) {
      errorMessage.value = 'Passwords do not match'
    } else {
      errorMessage.value = 'Please fill in all required fields correctly'
    }
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const success = await authStore.register({
      email: email.value,
      password: password.value,
      first_name: firstName.value,
      last_name: lastName.value,
      organization_name: organizationName.value,
      job_title: jobTitle.value || undefined,
      phone: phone.value || undefined
    })

    if (success) {
      successMessage.value = 'Account created successfully! Redirecting to dashboard...'
      setTimeout(() => {
        router.push('/dashboard')
      }, 1500)
    } else {
      errorMessage.value = authStore.error || 'Registration failed. Please try again.'
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'An unexpected error occurred'
  } finally {
    isLoading.value = false
  }
}

const handleKeyPress = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && isFormValid.value) {
    handleRegister()
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-cyan-50/30 py-12 px-4 sm:px-6 lg:px-8">
    <!-- Background decoration -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-gradient-to-br from-cyan-100 to-teal-100 opacity-50 blur-3xl"></div>
      <div class="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 opacity-50 blur-3xl"></div>
    </div>

    <div class="max-w-lg w-full space-y-8 relative">
      <!-- Logo and Title -->
      <div class="text-center">
        <div class="mx-auto h-16 w-16 flex items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500 to-teal-600 shadow-xl" style="box-shadow: 0 10px 40px -10px rgb(6 182 212 / 0.5);">
          <svg class="h-9 w-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
          </svg>
        </div>
        <h2 class="mt-6 text-3xl font-bold text-slate-800">
          DataMigrate AI
        </h2>
        <p class="mt-2 text-sm text-slate-500">
          Create your account and organization
        </p>
      </div>

      <!-- Register Form -->
      <div class="bg-white/80 backdrop-blur-sm shadow-xl rounded-2xl border border-gray-200/50 p-8">
        <form class="space-y-6" @submit.prevent="handleRegister">
          <!-- Personal Information Section -->
          <div>
            <div class="flex items-center mb-4">
              <div class="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-lg p-1.5 mr-2 shadow-sm">
                <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
              </div>
              <h3 class="text-lg font-semibold text-slate-800">Personal Information</h3>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <!-- First Name -->
              <div>
                <label for="first-name" class="block text-sm font-semibold text-slate-700 mb-1">First Name *</label>
                <input
                  id="first-name"
                  v-model="firstName"
                  name="first-name"
                  type="text"
                  autocomplete="given-name"
                  required
                  class="block w-full px-4 py-3 border border-gray-200 rounded-xl bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition-all duration-200"
                  placeholder="John"
                  @keypress="handleKeyPress"
                />
              </div>

              <!-- Last Name -->
              <div>
                <label for="last-name" class="block text-sm font-semibold text-slate-700 mb-1">Last Name *</label>
                <input
                  id="last-name"
                  v-model="lastName"
                  name="last-name"
                  type="text"
                  autocomplete="family-name"
                  required
                  class="block w-full px-4 py-3 border border-gray-200 rounded-xl bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition-all duration-200"
                  placeholder="Doe"
                  @keypress="handleKeyPress"
                />
              </div>
            </div>

            <!-- Email -->
            <div class="mt-4">
              <label for="email-address" class="block text-sm font-semibold text-slate-700 mb-1">Email Address *</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"/>
                  </svg>
                </div>
                <input
                  id="email-address"
                  v-model="email"
                  name="email"
                  type="email"
                  autocomplete="email"
                  required
                  class="block w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition-all duration-200"
                  placeholder="john@company.com"
                  @keypress="handleKeyPress"
                />
              </div>
            </div>

            <!-- Phone (Optional) -->
            <div class="mt-4">
              <label for="phone" class="block text-sm font-semibold text-slate-700 mb-1">Phone Number <span class="text-slate-400 font-normal">(optional)</span></label>
              <input
                id="phone"
                v-model="phone"
                name="phone"
                type="tel"
                autocomplete="tel"
                class="block w-full px-4 py-3 border border-gray-200 rounded-xl bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition-all duration-200"
                placeholder="+1 (555) 123-4567"
                @keypress="handleKeyPress"
              />
            </div>
          </div>

          <!-- Organization Section -->
          <div class="border-t border-gray-200 pt-6">
            <div class="flex items-center mb-4">
              <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg p-1.5 mr-2 shadow-sm">
                <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                </svg>
              </div>
              <h3 class="text-lg font-semibold text-slate-800">Organization</h3>
            </div>

            <!-- Organization Name -->
            <div>
              <label for="organization-name" class="block text-sm font-semibold text-slate-700 mb-1">Company / Organization Name *</label>
              <input
                id="organization-name"
                v-model="organizationName"
                name="organization-name"
                type="text"
                autocomplete="organization"
                required
                class="block w-full px-4 py-3 border border-gray-200 rounded-xl bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition-all duration-200"
                placeholder="Acme Corporation"
                @keypress="handleKeyPress"
              />
              <p class="mt-1 text-xs text-slate-500">You'll be the admin of this organization</p>
            </div>

            <!-- Job Title (Optional) -->
            <div class="mt-4">
              <label for="job-title" class="block text-sm font-semibold text-slate-700 mb-1">Job Title <span class="text-slate-400 font-normal">(optional)</span></label>
              <input
                id="job-title"
                v-model="jobTitle"
                name="job-title"
                type="text"
                autocomplete="organization-title"
                class="block w-full px-4 py-3 border border-gray-200 rounded-xl bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition-all duration-200"
                placeholder="Data Engineer"
                @keypress="handleKeyPress"
              />
            </div>
          </div>

          <!-- Password Section -->
          <div class="border-t border-gray-200 pt-6">
            <div class="flex items-center mb-4">
              <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg p-1.5 mr-2 shadow-sm">
                <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
              </div>
              <h3 class="text-lg font-semibold text-slate-800">Security</h3>
            </div>

            <!-- Password -->
            <div>
              <label for="password" class="block text-sm font-semibold text-slate-700 mb-1">Password *</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                  </svg>
                </div>
                <input
                  id="password"
                  v-model="password"
                  name="password"
                  type="password"
                  autocomplete="new-password"
                  required
                  :class="[
                    'block w-full pl-11 pr-4 py-3 border rounded-xl bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500 sm:text-sm transition-all duration-200',
                    password.length > 0 && !passwordLength ? 'border-red-300 focus:border-red-500' : 'border-gray-200 focus:border-cyan-500'
                  ]"
                  placeholder="Min 6 characters"
                  @keypress="handleKeyPress"
                />
              </div>

              <!-- Password Strength Meter -->
              <div v-if="password.length > 0" class="mt-3 p-3 bg-slate-50 rounded-xl">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs text-slate-500 font-medium">Password strength:</span>
                  <span :class="[
                    'text-xs font-semibold',
                    passwordStrength <= 2 ? 'text-red-600' : '',
                    passwordStrength === 3 ? 'text-amber-600' : '',
                    passwordStrength >= 4 ? 'text-emerald-600' : ''
                  ]">{{ passwordStrengthLabel }}</span>
                </div>
                <div class="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div
                    :class="['h-full transition-all duration-300 rounded-full', passwordStrengthColor]"
                    :style="{ width: (passwordStrength / 5 * 100) + '%' }"
                  ></div>
                </div>

                <!-- Password Requirements Checklist -->
                <div class="mt-3 grid grid-cols-2 gap-2">
                  <div class="flex items-center text-xs">
                    <div :class="['w-4 h-4 rounded-full flex items-center justify-center mr-2', passwordLength ? 'bg-emerald-100' : 'bg-gray-100']">
                      <svg v-if="passwordLength" class="w-3 h-3 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                      </svg>
                    </div>
                    <span :class="passwordLength ? 'text-emerald-600' : 'text-slate-500'">6+ characters</span>
                  </div>
                  <div class="flex items-center text-xs">
                    <div :class="['w-4 h-4 rounded-full flex items-center justify-center mr-2', passwordHasLetter ? 'bg-emerald-100' : 'bg-gray-100']">
                      <svg v-if="passwordHasLetter" class="w-3 h-3 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                      </svg>
                    </div>
                    <span :class="passwordHasLetter ? 'text-emerald-600' : 'text-slate-500'">Letter</span>
                  </div>
                  <div class="flex items-center text-xs">
                    <div :class="['w-4 h-4 rounded-full flex items-center justify-center mr-2', passwordHasNumber ? 'bg-emerald-100' : 'bg-gray-100']">
                      <svg v-if="passwordHasNumber" class="w-3 h-3 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                      </svg>
                    </div>
                    <span :class="passwordHasNumber ? 'text-emerald-600' : 'text-slate-500'">Number</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Confirm Password -->
            <div class="mt-4">
              <label for="confirm-password" class="block text-sm font-semibold text-slate-700 mb-1">Confirm Password *</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                  </svg>
                </div>
                <input
                  id="confirm-password"
                  v-model="confirmPassword"
                  name="confirm-password"
                  type="password"
                  autocomplete="new-password"
                  required
                  :class="[
                    'block w-full pl-11 pr-4 py-3 border rounded-xl bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 sm:text-sm transition-all duration-200',
                    confirmPassword.length > 0 && !passwordsMatch ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : '',
                    confirmPassword.length > 0 && passwordsMatch ? 'border-emerald-300 focus:border-emerald-500 focus:ring-emerald-500' : '',
                    confirmPassword.length === 0 ? 'border-gray-200 focus:border-cyan-500 focus:ring-cyan-500' : ''
                  ]"
                  placeholder="Re-enter password"
                  @keypress="handleKeyPress"
                />
              </div>

              <!-- Password Match Indicator -->
              <div v-if="confirmPassword.length > 0" class="mt-2 flex items-center text-xs">
                <div :class="['w-4 h-4 rounded-full flex items-center justify-center mr-2', passwordsMatch ? 'bg-emerald-100' : 'bg-red-100']">
                  <svg v-if="passwordsMatch" class="w-3 h-3 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                  </svg>
                  <svg v-else class="w-3 h-3 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                  </svg>
                </div>
                <span :class="passwordsMatch ? 'text-emerald-600' : 'text-red-600'">
                  {{ passwordsMatch ? 'Passwords match' : 'Passwords do not match' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="errorMessage" class="rounded-xl bg-gradient-to-r from-red-50 to-rose-50 border border-red-200 p-4">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm font-medium text-red-800">
                  {{ errorMessage }}
                </p>
              </div>
            </div>
          </div>

          <!-- Success Message -->
          <div v-if="successMessage" class="rounded-xl bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 p-4">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm font-medium text-emerald-800">
                  {{ successMessage }}
                </p>
              </div>
            </div>
          </div>

          <!-- Submit Button -->
          <div>
            <button
              type="submit"
              :disabled="!isFormValid || isLoading"
              class="group relative w-full flex justify-center py-3.5 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-[1.02]"
            >
              <span v-if="!isLoading">Create Account & Organization</span>
              <span v-else class="flex items-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                Creating account...
              </span>
            </button>
          </div>

          <!-- Sign In Link -->
          <div class="text-center">
            <p class="text-sm text-slate-600">
              Already have an account?
              <router-link to="/login" class="font-semibold text-cyan-600 hover:text-cyan-500 transition-colors">
                Sign in
              </router-link>
            </p>
          </div>
        </form>
      </div>

      <!-- Footer -->
      <div class="text-center">
        <p class="text-xs text-slate-400">
          By creating an account, you agree to our Terms of Service and Privacy Policy
        </p>
        <p class="text-xs text-slate-400 mt-2">
          2025 OKO Investments. All rights reserved.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional custom styles if needed */
</style>
