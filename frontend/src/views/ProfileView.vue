<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'

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
  <div class="min-h-screen bg-gray-100">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <h1 class="text-3xl font-bold text-gray-900">Profile</h1>
          <p class="mt-1 text-sm text-gray-500">
            Manage your account information and security settings
          </p>
        </div>
      </div>
    </div>

    <div class="px-4 sm:px-6 lg:px-8 py-8">
      <div class="max-w-4xl mx-auto space-y-8">
        <!-- Profile Header Card -->
        <div class="bg-white shadow rounded-lg overflow-hidden">
          <div class="bg-gradient-to-r from-indigo-500 to-purple-600 h-32"></div>
          <div class="px-6 pb-6">
            <div class="-mt-16 flex items-end space-x-6">
              <div class="h-32 w-32 rounded-full bg-indigo-600 flex items-center justify-center text-white text-4xl font-bold border-4 border-white shadow-lg">
                {{ getUserInitials() }}
              </div>
              <div class="pb-2">
                <h2 class="text-2xl font-bold text-gray-900">
                  {{ profile.firstName }} {{ profile.lastName }}
                </h2>
                <p class="text-gray-500">{{ profile.jobTitle || 'Team Member' }} at {{ profile.company }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Profile Information -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-5 border-b border-gray-200">
            <h2 class="text-lg font-medium text-gray-900">Profile Information</h2>
            <p class="mt-1 text-sm text-gray-500">
              Update your personal information
            </p>
          </div>

          <form @submit.prevent="updateProfile" class="px-6 py-5 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="firstName" class="block text-sm font-medium text-gray-700">
                  First Name
                </label>
                <input
                  id="firstName"
                  v-model="profile.firstName"
                  type="text"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              <div>
                <label for="lastName" class="block text-sm font-medium text-gray-700">
                  Last Name
                </label>
                <input
                  id="lastName"
                  v-model="profile.lastName"
                  type="text"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label for="email" class="block text-sm font-medium text-gray-700">
                Email Address
              </label>
              <input
                id="email"
                v-model="profile.email"
                type="email"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="company" class="block text-sm font-medium text-gray-700">
                  Company
                </label>
                <input
                  id="company"
                  v-model="profile.company"
                  type="text"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              <div>
                <label for="jobTitle" class="block text-sm font-medium text-gray-700">
                  Job Title
                </label>
                <input
                  id="jobTitle"
                  v-model="profile.jobTitle"
                  type="text"
                  placeholder="e.g. Data Engineer, CTO"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="timezone" class="block text-sm font-medium text-gray-700">
                  Timezone
                </label>
                <select
                  id="timezone"
                  v-model="profile.timezone"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="Europe/Copenhagen">Europe/Copenhagen (CET)</option>
                  <option value="Europe/London">Europe/London (GMT)</option>
                  <option value="America/New_York">America/New York (EST)</option>
                  <option value="America/Los_Angeles">America/Los Angeles (PST)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                </select>
              </div>

              <div>
                <label for="language" class="block text-sm font-medium text-gray-700">
                  Language
                </label>
                <select
                  id="language"
                  v-model="profile.language"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="en">English</option>
                  <option value="da">Danish</option>
                  <option value="de">German</option>
                  <option value="es">Spanish</option>
                </select>
              </div>
            </div>

            <div v-if="profileMessage" :class="[
              'p-3 rounded-md text-sm',
              profileMessage.includes('success') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
            ]">
              {{ profileMessage }}
            </div>

            <div class="flex justify-end">
              <button
                type="submit"
                :disabled="isUpdatingProfile"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
              >
                <svg v-if="isUpdatingProfile" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {{ isUpdatingProfile ? 'Saving...' : 'Save Changes' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Change Password -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-5 border-b border-gray-200">
            <h2 class="text-lg font-medium text-gray-900">Change Password</h2>
            <p class="mt-1 text-sm text-gray-500">
              Update your password to keep your account secure
            </p>
          </div>

          <form @submit.prevent="updatePassword" class="px-6 py-5 space-y-6">
            <div>
              <label for="currentPassword" class="block text-sm font-medium text-gray-700">
                Current Password
              </label>
              <input
                id="currentPassword"
                v-model="passwordForm.currentPassword"
                type="password"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="newPassword" class="block text-sm font-medium text-gray-700">
                  New Password
                </label>
                <input
                  id="newPassword"
                  v-model="passwordForm.newPassword"
                  type="password"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              <div>
                <label for="confirmPassword" class="block text-sm font-medium text-gray-700">
                  Confirm New Password
                </label>
                <input
                  id="confirmPassword"
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
            </div>

            <div v-if="passwordMessage" :class="[
              'p-3 rounded-md text-sm',
              passwordMessage.includes('success') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
            ]">
              {{ passwordMessage }}
            </div>

            <div class="flex justify-end">
              <button
                type="submit"
                :disabled="isUpdatingPassword"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
              >
                <svg v-if="isUpdatingPassword" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {{ isUpdatingPassword ? 'Updating...' : 'Update Password' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Activity Log -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-5 border-b border-gray-200">
            <h2 class="text-lg font-medium text-gray-900">Recent Activity</h2>
            <p class="mt-1 text-sm text-gray-500">
              Your recent account activity
            </p>
          </div>

          <ul class="divide-y divide-gray-200">
            <li v-for="activity in activityLog" :key="activity.id" class="px-6 py-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium text-gray-900">{{ activity.action }}</p>
                  <p class="text-sm text-gray-500">{{ activity.timestamp }}</p>
                </div>
                <span class="text-sm text-gray-400">{{ activity.ip }}</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
