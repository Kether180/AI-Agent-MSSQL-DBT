<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Navbar from '@/components/Navbar.vue'
import CustomerSupportWidget from '@/components/CustomerSupportWidget.vue'

const route = useRoute()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const showNavbar = computed(() => {
  // Don't show navbar on login page or 404 page
  const noNavbarRoutes = ['Login', 'NotFound', 'ForgotPassword', 'ResetPassword']
  return isAuthenticated.value && !noNavbarRoutes.includes(route.name as string)
})

const showSupportWidget = computed(() => {
  // Show support widget on all authenticated pages
  const noWidgetRoutes = ['Login', 'NotFound', 'ForgotPassword', 'ResetPassword']
  return isAuthenticated.value && !noWidgetRoutes.includes(route.name as string)
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navbar for authenticated users -->
    <Navbar v-if="showNavbar" />

    <!-- Main Content -->
    <main>
      <RouterView />
    </main>

    <!-- Global Customer Support Widget -->
    <CustomerSupportWidget v-if="showSupportWidget" />
  </div>
</template>

<style>
/* Global styles */
html, body {
  margin: 0;
  padding: 0;
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
}
</style>
