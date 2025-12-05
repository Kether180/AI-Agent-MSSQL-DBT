<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'

const { t } = useI18n()
const authStore = useAuthStore()

const user = computed(() => authStore.user)

// Form data - initialize from actual user data
const profile = ref({
  firstName: '',
  lastName: '',
  email: '',
  company: '',
  jobTitle: '',
  phone: '',
  timezone: 'Europe/Copenhagen',
  language: 'en'
})

// Initialize profile data from user
onMounted(() => {
  if (user.value) {
    profile.value = {
      firstName: user.value.first_name || '',
      lastName: user.value.last_name || '',
      email: user.value.email || '',
      company: user.value.organization?.name || '',
      jobTitle: user.value.job_title || '',
      phone: user.value.phone || '',
      timezone: 'Europe/Copenhagen',
      language: 'en'
    }
  }
})

// Password change
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const isUpdatingProfile = ref(false)
const isUpdatingPassword = ref(false)
const profileMessage = ref('')
const passwordMessage = ref('')

const getUserInitials = () => {
  return `${profile.value.firstName.charAt(0)}${profile.value.lastName.charAt(0)}`
}

const updateProfile = async () => {
  isUpdatingProfile.value = true
  profileMessage.value = ''

  try {
    const updatedUser = await api.updateProfile({
      first_name: profile.value.firstName,
      last_name: profile.value.lastName,
      email: profile.value.email,
      job_title: profile.value.jobTitle || undefined,
      phone: profile.value.phone || undefined
    })

    // Update the auth store with the new user data
    authStore.user = updatedUser
    profileMessage.value = 'Profile updated successfully!'
  } catch (error: any) {
    profileMessage.value = error.message || 'Failed to update profile'
  } finally {
    isUpdatingProfile.value = false
  }
}

const updatePassword = async () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordMessage.value = 'Passwords do not match'
    return
  }

  if (passwordForm.value.newPassword.length < 6) {
    passwordMessage.value = 'Password must be at least 6 characters'
    return
  }

  isUpdatingPassword.value = true
  passwordMessage.value = ''

  try {
    await api.changePassword({
      current_password: passwordForm.value.currentPassword,
      new_password: passwordForm.value.newPassword
    })
    passwordMessage.value = 'Password updated successfully!'
    passwordForm.value = { currentPassword: '', newPassword: '', confirmPassword: '' }
  } catch (error: any) {
    passwordMessage.value = error.message || 'Failed to update password'
  } finally {
    isUpdatingPassword.value = false
  }
}

// Activity log
const activityLog = ref([
  { id: 1, action: 'Login', timestamp: '2024-12-01 09:15:00', ip: '192.168.1.100' },
  { id: 2, action: 'Created migration "ecommerce-v2"', timestamp: '2024-11-30 14:22:00', ip: '192.168.1.100' },
  { id: 3, action: 'Updated profile settings', timestamp: '2024-11-29 11:05:00', ip: '192.168.1.100' },
  { id: 4, action: 'Added database connection', timestamp: '2024-11-28 16:30:00', ip: '192.168.1.100' },
  { id: 5, action: 'Login', timestamp: '2024-11-28 09:00:00', ip: '192.168.1.105' }
])
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/30">
    <!-- Header with gradient -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-8">
          <div class="flex items-center">
            <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-3 mr-4 shadow-lg shadow-indigo-500/25">
              <svg class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            <div>
              <h1 class="text-3xl font-bold text-white">{{ t('profile.title') }}</h1>
              <p class="mt-1 text-slate-300">
                {{ t('profile.subtitle') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <div class="max-w-4xl mx-auto space-y-8">
        <!-- Profile Header Card -->
        <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
          <div class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 h-32 relative">
            <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/10"></div>
          </div>
          <div class="px-6 pb-6">
            <div class="-mt-16 flex items-end space-x-6">
              <div class="h-32 w-32 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-4xl font-bold border-4 border-white shadow-xl" style="box-shadow: 0 10px 40px -10px rgb(99 102 241 / 0.5);">
                {{ getUserInitials() }}
              </div>
              <div class="pb-2">
                <h2 class="text-2xl font-bold text-slate-800">
                  {{ profile.firstName }} {{ profile.lastName }}
                </h2>
                <p class="text-slate-500">{{ profile.jobTitle || t('profile.teamMember') }} at {{ profile.company }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Profile Information -->
        <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
          <div class="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-slate-50 to-white">
            <div class="flex items-center">
              <div class="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-lg p-2 mr-3 shadow-lg shadow-cyan-500/25">
                <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div>
                <h2 class="text-lg font-semibold text-slate-800">{{ t('profile.profileInfo') }}</h2>
                <p class="text-sm text-slate-500">
                  {{ t('profile.updatePersonalInfo') }}
                </p>
              </div>
            </div>
          </div>

          <form @submit.prevent="updateProfile" class="px-6 py-5 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="firstName" class="block text-sm font-semibold text-slate-700 mb-1">
                  {{ t('profile.firstName') }}
                </label>
                <input
                  id="firstName"
                  v-model="profile.firstName"
                  type="text"
                  class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
                />
              </div>

              <div>
                <label for="lastName" class="block text-sm font-semibold text-slate-700 mb-1">
                  {{ t('profile.lastName') }}
                </label>
                <input
                  id="lastName"
                  v-model="profile.lastName"
                  type="text"
                  class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
                />
              </div>
            </div>

            <div>
              <label for="email" class="block text-sm font-semibold text-slate-700 mb-1">
                {{ t('profile.emailAddress') }}
              </label>
              <input
                id="email"
                v-model="profile.email"
                type="email"
                class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
              />
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="company" class="block text-sm font-semibold text-slate-700 mb-1">
                  {{ t('profile.company') }}
                </label>
                <input
                  id="company"
                  v-model="profile.company"
                  type="text"
                  class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
                />
              </div>

              <div>
                <label for="jobTitle" class="block text-sm font-semibold text-slate-700 mb-1">
                  {{ t('profile.jobTitle') }}
                </label>
                <input
                  id="jobTitle"
                  v-model="profile.jobTitle"
                  type="text"
                  :placeholder="t('profile.jobTitlePlaceholder')"
                  class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
                />
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="timezone" class="block text-sm font-semibold text-slate-700 mb-1">
                  {{ t('profile.timezone') }}
                </label>
                <select
                  id="timezone"
                  v-model="profile.timezone"
                  class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
                >
                  <option value="Europe/Copenhagen">Europe/Copenhagen (CET)</option>
                  <option value="Europe/London">Europe/London (GMT)</option>
                  <option value="America/New_York">America/New York (EST)</option>
                  <option value="America/Los_Angeles">America/Los Angeles (PST)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                </select>
              </div>

              <div>
                <label for="language" class="block text-sm font-semibold text-slate-700 mb-1">
                  {{ t('profile.language') }}
                </label>
                <select
                  id="language"
                  v-model="profile.language"
                  class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
                >
                  <option value="en">English</option>
                  <option value="da">Danish</option>
                  <option value="de">German</option>
                  <option value="es">Spanish</option>
                </select>
              </div>
            </div>

            <div v-if="profileMessage" :class="[
              'p-4 rounded-xl text-sm font-medium',
              profileMessage.includes('success') ? 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-800 border border-emerald-200' : 'bg-gradient-to-r from-red-50 to-rose-50 text-red-800 border border-red-200'
            ]">
              <div class="flex items-center">
                <svg v-if="profileMessage.includes('success')" class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <svg v-else class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                {{ profileMessage }}
              </div>
            </div>

            <div class="flex justify-end">
              <button
                type="submit"
                :disabled="isUpdatingProfile"
                class="inline-flex items-center px-5 py-2.5 border border-transparent shadow-lg text-sm font-medium rounded-xl text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 disabled:opacity-50 transition-all duration-200 hover:shadow-xl hover:scale-105"
              >
                <svg v-if="isUpdatingProfile" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {{ isUpdatingProfile ? t('profile.saving') : t('profile.saveChanges') }}
              </button>
            </div>
          </form>
        </div>

        <!-- Change Password -->
        <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
          <div class="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-slate-50 to-white">
            <div class="flex items-center">
              <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg p-2 mr-3 shadow-lg shadow-amber-500/25">
                <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
              </div>
              <div>
                <h2 class="text-lg font-semibold text-slate-800">{{ t('profile.changePassword') }}</h2>
                <p class="text-sm text-slate-500">
                  {{ t('profile.keepAccountSecure') }}
                </p>
              </div>
            </div>
          </div>

          <form @submit.prevent="updatePassword" class="px-6 py-5 space-y-6">
            <div>
              <label for="currentPassword" class="block text-sm font-semibold text-slate-700 mb-1">
                {{ t('profile.currentPassword') }}
              </label>
              <input
                id="currentPassword"
                v-model="passwordForm.currentPassword"
                type="password"
                class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
              />
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="newPassword" class="block text-sm font-semibold text-slate-700 mb-1">
                  {{ t('profile.newPasswordLabel') }}
                </label>
                <input
                  id="newPassword"
                  v-model="passwordForm.newPassword"
                  type="password"
                  class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
                />
              </div>

              <div>
                <label for="confirmPassword" class="block text-sm font-semibold text-slate-700 mb-1">
                  {{ t('profile.confirmNewPassword') }}
                </label>
                <input
                  id="confirmPassword"
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  class="block w-full rounded-xl border-gray-200 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm px-4 py-3 bg-slate-50 focus:bg-white transition-colors"
                />
              </div>
            </div>

            <div v-if="passwordMessage" :class="[
              'p-4 rounded-xl text-sm font-medium',
              passwordMessage.includes('success') ? 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-800 border border-emerald-200' : 'bg-gradient-to-r from-red-50 to-rose-50 text-red-800 border border-red-200'
            ]">
              <div class="flex items-center">
                <svg v-if="passwordMessage.includes('success')" class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <svg v-else class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                {{ passwordMessage }}
              </div>
            </div>

            <div class="flex justify-end">
              <button
                type="submit"
                :disabled="isUpdatingPassword"
                class="inline-flex items-center px-5 py-2.5 border border-transparent shadow-lg text-sm font-medium rounded-xl text-white bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 disabled:opacity-50 transition-all duration-200 hover:shadow-xl hover:scale-105"
              >
                <svg v-if="isUpdatingPassword" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {{ isUpdatingPassword ? t('profile.updating') : t('profile.updatePassword') }}
              </button>
            </div>
          </form>
        </div>

        <!-- Activity Log -->
        <div class="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl border border-gray-200/50 overflow-hidden">
          <div class="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-slate-50 to-white">
            <div class="flex items-center">
              <div class="bg-gradient-to-br from-slate-600 to-slate-700 rounded-lg p-2 mr-3 shadow-lg shadow-slate-500/25">
                <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div>
                <h2 class="text-lg font-semibold text-slate-800">{{ t('profile.recentActivity') }}</h2>
                <p class="text-sm text-slate-500">
                  {{ t('profile.yourRecentActivity') }}
                </p>
              </div>
            </div>
          </div>

          <ul class="divide-y divide-gray-100">
            <li v-for="activity in activityLog" :key="activity.id" class="px-6 py-4 hover:bg-gradient-to-r hover:from-slate-50 hover:to-transparent transition-colors">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center mr-4">
                    <svg class="h-5 w-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path v-if="activity.action.includes('Login')" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
                      <path v-else-if="activity.action.includes('migration')" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                      <path v-else-if="activity.action.includes('profile')" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                      <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                    </svg>
                  </div>
                  <div>
                    <p class="text-sm font-semibold text-slate-800">{{ activity.action }}</p>
                    <p class="text-sm text-slate-500">{{ activity.timestamp }}</p>
                  </div>
                </div>
                <span class="text-sm text-slate-400 font-mono bg-slate-100 px-2 py-1 rounded">{{ activity.ip }}</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
