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
  if (passwordStrength.value <= 2) return 'bg-red-500'
  if (passwordStrength.value <= 3) return 'bg-yellow-500'
  if (passwordStrength.value <= 4) return 'bg-green-500'
  return 'bg-emerald-500'
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
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-lg w-full space-y-8">
      <!-- Logo and Title -->
      <div>
        <div class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-indigo-600">
          <svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
          </svg>
        </div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          DataMigrate AI
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Create your account and organization
        </p>
      </div>

      <!-- Register Form -->
      <form class="mt-8 space-y-6" @submit.prevent="handleRegister">
        <!-- Personal Information Section -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
          <div class="grid grid-cols-2 gap-4">
            <!-- First Name -->
            <div>
              <label for="first-name" class="block text-sm font-medium text-gray-700">First Name *</label>
              <input
                id="first-name"
                v-model="firstName"
                name="first-name"
                type="text"
                autocomplete="given-name"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="John"
                @keypress="handleKeyPress"
              />
            </div>

            <!-- Last Name -->
            <div>
              <label for="last-name" class="block text-sm font-medium text-gray-700">Last Name *</label>
              <input
                id="last-name"
                v-model="lastName"
                name="last-name"
                type="text"
                autocomplete="family-name"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Doe"
                @keypress="handleKeyPress"
              />
            </div>
          </div>

          <!-- Email -->
          <div class="mt-4">
            <label for="email-address" class="block text-sm font-medium text-gray-700">Email Address *</label>
            <input
              id="email-address"
              v-model="email"
              name="email"
              type="email"
              autocomplete="email"
              required
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="john@company.com"
              @keypress="handleKeyPress"
            />
          </div>

          <!-- Phone (Optional) -->
          <div class="mt-4">
            <label for="phone" class="block text-sm font-medium text-gray-700">Phone Number <span class="text-gray-400">(optional)</span></label>
            <input
              id="phone"
              v-model="phone"
              name="phone"
              type="tel"
              autocomplete="tel"
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="+1 (555) 123-4567"
              @keypress="handleKeyPress"
            />
          </div>
        </div>

        <!-- Organization Section -->
        <div class="border-t border-gray-200 pt-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Organization</h3>

          <!-- Organization Name -->
          <div>
            <label for="organization-name" class="block text-sm font-medium text-gray-700">Company / Organization Name *</label>
            <input
              id="organization-name"
              v-model="organizationName"
              name="organization-name"
              type="text"
              autocomplete="organization"
              required
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Acme Corporation"
              @keypress="handleKeyPress"
            />
            <p class="mt-1 text-xs text-gray-500">You'll be the admin of this organization</p>
          </div>

          <!-- Job Title (Optional) -->
          <div class="mt-4">
            <label for="job-title" class="block text-sm font-medium text-gray-700">Job Title <span class="text-gray-400">(optional)</span></label>
            <input
              id="job-title"
              v-model="jobTitle"
              name="job-title"
              type="text"
              autocomplete="organization-title"
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Data Engineer"
              @keypress="handleKeyPress"
            />
          </div>
        </div>

        <!-- Password Section -->
        <div class="border-t border-gray-200 pt-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Security</h3>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">Password *</label>
            <input
              id="password"
              v-model="password"
              name="password"
              type="password"
              autocomplete="new-password"
              required
              :class="[
                'mt-1 appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                password.length > 0 && !passwordLength ? 'border-red-500' : 'border-gray-300'
              ]"
              placeholder="Min 6 characters"
              @keypress="handleKeyPress"
            />

            <!-- Password Strength Meter -->
            <div v-if="password.length > 0" class="mt-2">
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs text-gray-500">Password strength:</span>
                <span :class="[
                  'text-xs font-medium',
                  passwordStrength <= 2 ? 'text-red-600' : '',
                  passwordStrength === 3 ? 'text-yellow-600' : '',
                  passwordStrength >= 4 ? 'text-green-600' : ''
                ]">{{ passwordStrengthLabel }}</span>
              </div>
              <div class="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
                <div
                  :class="['h-full transition-all duration-300', passwordStrengthColor]"
                  :style="{ width: (passwordStrength / 5 * 100) + '%' }"
                ></div>
              </div>
            </div>

            <!-- Password Requirements Checklist -->
            <div class="mt-3 space-y-1">
              <div class="flex items-center text-xs">
                <svg v-if="passwordLength" class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                </svg>
                <svg v-else class="w-4 h-4 text-gray-300 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clip-rule="evenodd"/>
                </svg>
                <span :class="passwordLength ? 'text-green-600' : 'text-gray-500'">At least 6 characters</span>
              </div>
              <div class="flex items-center text-xs">
                <svg v-if="passwordHasLetter" class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                </svg>
                <svg v-else class="w-4 h-4 text-gray-300 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clip-rule="evenodd"/>
                </svg>
                <span :class="passwordHasLetter ? 'text-green-600' : 'text-gray-500'">Contains a letter</span>
              </div>
              <div class="flex items-center text-xs">
                <svg v-if="passwordHasNumber" class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                </svg>
                <svg v-else class="w-4 h-4 text-gray-300 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clip-rule="evenodd"/>
                </svg>
                <span :class="passwordHasNumber ? 'text-green-600' : 'text-gray-500'">Contains a number</span>
              </div>
            </div>
          </div>

          <!-- Confirm Password -->
          <div class="mt-4">
            <label for="confirm-password" class="block text-sm font-medium text-gray-700">Confirm Password *</label>
            <input
              id="confirm-password"
              v-model="confirmPassword"
              name="confirm-password"
              type="password"
              autocomplete="new-password"
              required
              :class="[
                'mt-1 appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                confirmPassword.length > 0 && !passwordsMatch ? 'border-red-500' : '',
                confirmPassword.length > 0 && passwordsMatch ? 'border-green-500' : '',
                confirmPassword.length === 0 ? 'border-gray-300' : ''
              ]"
              placeholder="Re-enter password"
              @keypress="handleKeyPress"
            />

            <!-- Password Match Indicator -->
            <div v-if="confirmPassword.length > 0" class="mt-2 flex items-center text-xs">
              <svg v-if="passwordsMatch" class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
              </svg>
              <svg v-else class="w-4 h-4 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
              <span :class="passwordsMatch ? 'text-green-600' : 'text-red-600'">
                {{ passwordsMatch ? 'Passwords match' : 'Passwords do not match' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="rounded-md bg-red-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
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
        <div v-if="successMessage" class="rounded-md bg-green-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-green-800">
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
            class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
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
          <p class="text-sm text-gray-600">
            Already have an account?
            <router-link to="/login" class="font-medium text-indigo-600 hover:text-indigo-500">
              Sign in
            </router-link>
          </p>
        </div>
      </form>

      <!-- Footer -->
      <div class="text-center">
        <p class="text-xs text-gray-500">
          By creating an account, you agree to our Terms of Service and Privacy Policy
        </p>
        <p class="text-xs text-gray-500 mt-2">
          © 2025 OKO Investments. All rights reserved.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional custom styles if needed */
</style>
