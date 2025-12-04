<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '@/services/api'

const router = useRouter()
const route = useRoute()

const token = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const tokenValid = ref(true)

onMounted(() => {
  const tokenParam = route.query.token as string
  if (!tokenParam) {
    tokenValid.value = false
    errorMessage.value = 'Invalid or missing reset token. Please request a new password reset.'
  } else {
    token.value = tokenParam
  }
})

const passwordsMatch = computed(() => {
  return password.value === confirmPassword.value
})

const isFormValid = computed(() => {
  return password.value.length >= 8 && passwordsMatch.value && tokenValid.value
})

const handleResetPassword = async () => {
  if (!isFormValid.value) {
    if (!passwordsMatch.value) {
      errorMessage.value = 'Passwords do not match'
    } else if (password.value.length < 8) {
      errorMessage.value = 'Password must be at least 8 characters'
    }
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    await api.resetPassword(token.value, password.value)
    successMessage.value = 'Your password has been reset successfully!'

    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (error: any) {
    errorMessage.value = error.message || 'Failed to reset password. The link may have expired.'
  } finally {
    isLoading.value = false
  }
}

const handleKeyPress = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && isFormValid.value) {
    handleResetPassword()
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <!-- Logo and Title -->
      <div>
        <div class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-indigo-600">
          <svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
          </svg>
        </div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Reset Your Password
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Enter your new password below
        </p>
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
            <p class="text-sm text-green-700 mt-1">
              Redirecting to login...
            </p>
          </div>
        </div>
      </div>

      <!-- Reset Form -->
      <form v-if="!successMessage" class="mt-8 space-y-6" @submit.prevent="handleResetPassword">
        <div class="rounded-md shadow-sm -space-y-px">
          <!-- New Password Input -->
          <div>
            <label for="password" class="sr-only">New Password</label>
            <input
              id="password"
              v-model="password"
              name="password"
              type="password"
              autocomplete="new-password"
              required
              :disabled="!tokenValid"
              class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="New password (min 8 characters)"
              @keypress="handleKeyPress"
            />
          </div>

          <!-- Confirm Password Input -->
          <div>
            <label for="confirm-password" class="sr-only">Confirm Password</label>
            <input
              id="confirm-password"
              v-model="confirmPassword"
              name="confirm-password"
              type="password"
              autocomplete="new-password"
              required
              :disabled="!tokenValid"
              class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="Confirm new password"
              @keypress="handleKeyPress"
            />
          </div>
        </div>

        <!-- Password Match Indicator -->
        <div v-if="confirmPassword && !passwordsMatch" class="text-sm text-red-600">
          Passwords do not match
        </div>
        <div v-if="confirmPassword && passwordsMatch && password.length >= 8" class="text-sm text-green-600">
          Passwords match
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

        <!-- Submit Button -->
        <div>
          <button
            type="submit"
            :disabled="!isFormValid || isLoading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="!isLoading">Reset Password</span>
            <span v-else class="flex items-center">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              Resetting...
            </span>
          </button>
        </div>

        <!-- Back to Login Link -->
        <div class="text-center">
          <p class="text-sm text-gray-600">
            Remember your password?
            <router-link to="/login" class="font-medium text-indigo-600 hover:text-indigo-500">
              Back to login
            </router-link>
          </p>
        </div>
      </form>

      <!-- Footer -->
      <div class="text-center">
        <p class="text-xs text-gray-500">
          © 2025 OKO Investments. All rights reserved.
        </p>
        <p class="text-xs text-gray-500 mt-1">
          Built by Alexander Garcia Angus
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional custom styles if needed */
</style>
