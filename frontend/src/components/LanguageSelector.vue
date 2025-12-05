<template>
  <div class="relative">
    <button
      @click="isOpen = !isOpen"
      class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-slate-600 transition-all"
    >
      <span class="text-base leading-none">{{ currentLocale?.flag }}</span>
      <span class="text-sm text-slate-300 hidden sm:inline leading-none">{{ currentLocale?.name }}</span>
      <svg
        class="w-4 h-4 text-slate-400 transition-transform ml-0.5"
        :class="{ 'rotate-180': isOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 mt-2 w-48 rounded-xl bg-slate-800/95 backdrop-blur-xl border border-slate-700/50 shadow-xl z-50 overflow-hidden"
      >
        <div class="py-2">
          <button
            v-for="locale in LOCALES"
            :key="locale.code"
            @click="selectLocale(locale.code)"
            class="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-slate-700/50 transition-colors"
            :class="{ 'bg-slate-700/30': locale.code === currentLocale?.code }"
          >
            <span class="text-base leading-none">{{ locale.flag }}</span>
            <span class="text-sm text-slate-200 flex-1">{{ locale.name }}</span>
            <span class="text-xs font-mono text-slate-500 uppercase">{{ locale.code }}</span>
            <svg
              v-if="locale.code === currentLocale?.code"
              class="w-4 h-4 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { LOCALES, setLocale, type Locale } from '@/i18n'

const { locale } = useI18n()
const isOpen = ref(false)

const currentLocale = computed(() => {
  return LOCALES.find(l => l.code === locale.value)
})

function selectLocale(code: Locale) {
  setLocale(code)
  isOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.relative')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
