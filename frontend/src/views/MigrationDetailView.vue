<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
const migrationId = route.params.id
</script>

<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Migration Details</h1>
    <p class="text-gray-600">Migration ID: {{ migrationId }}</p>
    <div class="mt-4 p-4 bg-gray-100 rounded">
      <p>Migration details will be displayed here.</p>
    </div>
  </div>
</template>
