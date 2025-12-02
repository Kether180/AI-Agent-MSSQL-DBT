<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="text-center">
      <h1 class="text-6xl font-bold text-gray-800">404</h1>
      <p class="mt-4 text-xl text-gray-600">Page not found</p>
      <p class="mt-2 text-gray-500">The page you're looking for doesn't exist.</p>
      <button
        @click="router.push('/')"
        class="mt-6 px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Go Home
      </button>
    </div>
  </div>
</template>
