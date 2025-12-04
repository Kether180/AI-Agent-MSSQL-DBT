<script setup lang="ts">
import { ref, computed } from 'vue'
import { api } from '@/services/api'

const email = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const isFormValid = computed(() => {
  return email.value.length > 0 && email.value.includes('@')
})

const handleForgotPassword = async () => {
  if (!isFormValid.value) {
    errorMessage.value = 'Please enter a valid email address'
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    await api.forgotPassword(email.value)
    successMessage.value = 'If an account exists with this email, you will receive a password reset link shortly.'
    email.value = ''
  } catch (error: any) {
    // Show generic message for security (don't reveal if email exists)
    successMessage.value = 'If an account exists with this email, you will receive a password reset link shortly.'
  } finally {
    isLoading.value = false
  }
}

const handleKeyPress = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && isFormValid.value) {
    handleForgotPassword()
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
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
        </div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Forgot Password?
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Enter your email and we'll send you a reset link
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
            <p class="text-sm text-green-700 mt-2">
              Check your inbox and spam folder for the reset link. The link expires in 1 hour.
            </p>
          </div>
        </div>
      </div>

      <!-- Forgot Password Form -->
      <form v-if="!successMessage" class="mt-8 space-y-6" @submit.prevent="handleForgotPassword">
        <div class="rounded-md shadow-sm">
          <!-- Email Input -->
          <div>
            <label for="email-address" class="sr-only">Email address</label>
            <input
              id="email-address"
              v-model="email"
              name="email"
              type="email"
              autocomplete="email"
              required
              class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              placeholder="Email address"
              @keypress="handleKeyPress"
            />
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

        <!-- Submit Button -->
        <div>
          <button
            type="submit"
            :disabled="!isFormValid || isLoading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="!isLoading">Send Reset Link</span>
            <span v-else class="flex items-center">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              Sending...
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

      <!-- After Success - Back to Login -->
      <div v-if="successMessage" class="text-center">
        <router-link to="/login" class="inline-flex items-center font-medium text-indigo-600 hover:text-indigo-500">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
          </svg>
          Back to login
        </router-link>
      </div>

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
