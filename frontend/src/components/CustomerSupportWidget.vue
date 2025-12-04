<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { api } from '@/services/api'
import { marked } from 'marked'

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,
  gfm: true
})

const isChatOpen = ref(false)
const message = ref('')
const chatMessages = ref<{ role: 'user' | 'assistant'; content: string }[]>([
  { role: 'assistant', content: 'Hello! I\'m your AI Support Assistant. How can I help you with DataMigrate AI today?' }
])
const isLoading = ref(false)
const hasError = ref(false)
const chatContainer = ref<HTMLElement | null>(null)
const hasNewMessage = ref(true)

// Fallback responses when API is unavailable
const fallbackResponses = [
  'I can help you with that! Could you provide more details about your migration requirements?',
  'Great question! DataMigrate AI supports MSSQL to dbt migrations with automatic schema analysis.',
  'To create a new migration, go to Migrations > New Migration and follow the wizard steps.',
  'Our AI agents can automatically generate dbt models, tests, and documentation for your data.',
  'If you\'re experiencing connection issues, please verify your SQL Server credentials and network settings.',
  'You can use the DataPrep Agent to profile and clean your data before migration.',
  'The ML Fine-Tuning agent helps optimize model performance for your specific data patterns.',
  'Check the Documentation section for detailed guides on all features.'
]

const toggleChat = () => {
  isChatOpen.value = !isChatOpen.value
  if (isChatOpen.value) {
    hasNewMessage.value = false
  }
}

// Scroll to bottom when new messages arrive
watch(chatMessages, () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}, { deep: true })

const sendMessage = async () => {
  if (!message.value.trim() || isLoading.value) return

  const userMessage = message.value.trim()
  chatMessages.value.push({ role: 'user', content: userMessage })
  message.value = ''
  isLoading.value = true
  hasError.value = false

  try {
    // Get conversation history (exclude the welcome message for API)
    const history = chatMessages.value.slice(1, -1) // Exclude welcome and current message

    // Call the real API
    const response = await api.sendChatMessage(userMessage, history)

    chatMessages.value.push({
      role: 'assistant',
      content: response.response
    })
  } catch (error) {
    console.error('Chat API error:', error)
    hasError.value = true

    // Use intelligent fallback based on keywords in the message
    let fallbackResponse = getFallbackResponse(userMessage)

    chatMessages.value.push({
      role: 'assistant',
      content: fallbackResponse
    })
  } finally {
    isLoading.value = false
  }
}

// Get contextual fallback response based on user's message
const getFallbackResponse = (userMessage: string): string => {
  const lowerMessage = userMessage.toLowerCase()

  if (lowerMessage.includes('migration') || lowerMessage.includes('migrate')) {
    return 'To create a new migration, navigate to the Migrations page and click "New Migration". The wizard will guide you through connecting to your MSSQL database, selecting tables, and configuring your dbt project settings.'
  }
  if (lowerMessage.includes('connect') || lowerMessage.includes('database') || lowerMessage.includes('mssql')) {
    return 'For database connections, you can use either SQL Server authentication or Windows Authentication. Go to Settings > Connections to add a new connection. Make sure your SQL Server allows remote connections and the firewall permits access on port 1433.'
  }
  if (lowerMessage.includes('dbt') || lowerMessage.includes('model')) {
    return 'DataMigrate AI automatically generates dbt models from your MSSQL schema. It creates staging models, intermediate transformations, and can include tests and documentation. You can customize the target warehouse (Snowflake, BigQuery, Fabric, etc.) during migration setup.'
  }
  if (lowerMessage.includes('agent') || lowerMessage.includes('ai')) {
    return 'We have several AI agents available: DataPrep Agent for data profiling and cleaning, ML Fine-Tuning Agent for optimizing transformations, Data Quality Agent for validation, and more. Access them from the Dashboard or navigate to /agents.'
  }
  if (lowerMessage.includes('error') || lowerMessage.includes('fail') || lowerMessage.includes('problem')) {
    return 'I\'m sorry you\'re experiencing issues. Common solutions include: 1) Verify your database credentials, 2) Check network connectivity to SQL Server, 3) Ensure the user has read permissions on the database. For persistent issues, check the migration logs or contact support.'
  }
  if (lowerMessage.includes('help') || lowerMessage.includes('how')) {
    return 'I can help you with: creating migrations, configuring database connections, understanding dbt models, using AI agents, and troubleshooting issues. What would you like to know more about?'
  }

  // Random fallback for other queries
  const randomIndex = Math.floor(Math.random() * fallbackResponses.length)
  return fallbackResponses[randomIndex] ?? fallbackResponses[0] ?? 'How can I help you today?'
}

const handleKeyPress = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const clearChat = () => {
  chatMessages.value = [
    { role: 'assistant', content: 'Hello! I\'m your AI Support Assistant. How can I help you with DataMigrate AI today?' }
  ]
  hasError.value = false
}

// Render markdown to HTML
const renderMarkdown = (content: string): string => {
  const result = marked(content)
  return typeof result === 'string' ? result : ''
}

// Request a callback from support
const requestCallback = () => {
  chatMessages.value.push({
    role: 'assistant',
    content: `## 📞 Request a Callback

To speak with a support representative, please provide:

1. **Your Name**
2. **Phone Number** (with country code)
3. **Best time to call**
4. **Brief description of your issue**

You can either:
- **Reply here** with your details and we'll arrange a callback
- **Email us** at [support@datamigrate.ai](mailto:support@datamigrate.ai)
- **Call directly**: +45 6127 5393 (Mon-Fri, 9am-5pm CET)

Our support team typically responds within 2-4 business hours.`
  })
}
</script>

<template>
  <!-- Customer Support Chat Widget (Floating) -->
  <div class="fixed bottom-6 right-6 z-50">
    <!-- Chat Window -->
    <transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="transform opacity-0 scale-95 translate-y-4"
      enter-to-class="transform opacity-100 scale-100 translate-y-0"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="transform opacity-100 scale-100 translate-y-0"
      leave-to-class="transform opacity-0 scale-95 translate-y-4"
    >
      <div
        v-if="isChatOpen"
        class="absolute bottom-20 right-0 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden"
      >
        <!-- Chat Header -->
        <div class="bg-gradient-to-r from-cyan-500 to-teal-600 px-4 py-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center mr-3">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                </svg>
              </div>
              <div>
                <h3 class="text-white font-semibold">AI Support Assistant</h3>
                <p class="text-cyan-100 text-xs">Always here to help</p>
              </div>
            </div>
            <div class="flex items-center space-x-1">
              <!-- Clear chat button -->
              <button
                @click="clearChat"
                class="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
                title="Clear chat"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
              <!-- Close button -->
              <button
                @click="toggleChat"
                class="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Error banner -->
        <div v-if="hasError" class="bg-amber-50 border-b border-amber-200 px-4 py-2">
          <p class="text-xs text-amber-700 flex items-center">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            Using offline mode - responses may be limited
          </p>
        </div>

        <!-- Chat Messages -->
        <div
          ref="chatContainer"
          class="h-80 overflow-y-auto p-4 space-y-4 bg-slate-50"
        >
          <div
            v-for="(msg, index) in chatMessages"
            :key="index"
            :class="[
              'flex',
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            ]"
          >
            <div
              :class="[
                'max-w-[80%] px-4 py-2 rounded-2xl text-sm',
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-cyan-500 to-teal-600 text-white rounded-br-md'
                  : 'bg-white text-slate-700 border border-slate-200 rounded-bl-md shadow-sm chat-markdown'
              ]"
              v-html="msg.role === 'assistant' ? renderMarkdown(msg.content) : msg.content"
            ></div>
          </div>
          <!-- Loading indicator -->
          <div v-if="isLoading" class="flex justify-start">
            <div class="bg-white text-slate-700 border border-slate-200 rounded-2xl rounded-bl-md shadow-sm px-4 py-3">
              <div class="flex space-x-1">
                <div class="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                <div class="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                <div class="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="px-4 py-2 bg-slate-50 border-t border-slate-200 flex items-center justify-center space-x-3">
          <button
            @click="requestCallback"
            class="flex items-center text-xs text-slate-600 hover:text-cyan-600 transition-colors"
            title="Request a callback"
          >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
            </svg>
            Request Callback
          </button>
          <span class="text-slate-300">|</span>
          <a
            href="mailto:support@datamigrate.ai?subject=Support%20Request"
            class="flex items-center text-xs text-slate-600 hover:text-cyan-600 transition-colors"
            title="Email support"
          >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
            Email Us
          </a>
        </div>

        <!-- Chat Input -->
        <div class="p-4 bg-white border-t border-slate-200">
          <div class="flex items-center space-x-2">
            <input
              v-model="message"
              @keypress="handleKeyPress"
              type="text"
              placeholder="Ask about migrations, dbt, agents..."
              class="flex-1 px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
              :disabled="isLoading"
            />
            <button
              @click="sendMessage"
              :disabled="!message.trim() || isLoading"
              class="p-2 bg-gradient-to-r from-cyan-500 to-teal-600 text-white rounded-xl hover:from-cyan-600 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Chat Toggle Button -->
    <button
      @click="toggleChat"
      :class="[
        'group relative flex items-center justify-center w-16 h-16 rounded-full shadow-2xl transition-all duration-300',
        isChatOpen
          ? 'bg-slate-700 hover:bg-slate-800 shadow-slate-500/40'
          : 'bg-gradient-to-br from-cyan-500 to-teal-600 shadow-cyan-500/40 hover:shadow-cyan-500/60 hover:scale-110'
      ]"
    >
      <svg v-if="!isChatOpen" class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
      </svg>
      <svg v-else class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
      </svg>

      <!-- Notification dot (only when chat is closed and has new messages) -->
      <span v-if="!isChatOpen && hasNewMessage" class="absolute -top-1 -right-1 flex h-5 w-5">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-5 w-5 bg-red-500 text-white text-xs font-bold items-center justify-center">1</span>
      </span>

      <!-- Tooltip (only when chat is closed) -->
      <span v-if="!isChatOpen" class="absolute right-20 bg-slate-800 text-white text-sm px-3 py-2 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 shadow-lg">
        AI Support Assistant
        <span class="absolute right-[-6px] top-1/2 -translate-y-1/2 border-8 border-transparent border-l-slate-800"></span>
      </span>
    </button>
  </div>
</template>

<style scoped>
/* Markdown styling for chat messages */
.chat-markdown :deep(p) {
  margin: 0 0 0.5rem 0;
}
.chat-markdown :deep(p:last-child) {
  margin-bottom: 0;
}
.chat-markdown :deep(h1),
.chat-markdown :deep(h2),
.chat-markdown :deep(h3) {
  font-weight: 600;
  margin: 0.75rem 0 0.5rem 0;
  line-height: 1.3;
}
.chat-markdown :deep(h2) {
  font-size: 1rem;
}
.chat-markdown :deep(h3) {
  font-size: 0.9rem;
}
.chat-markdown :deep(ul),
.chat-markdown :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}
.chat-markdown :deep(li) {
  margin: 0.25rem 0;
}
.chat-markdown :deep(strong) {
  font-weight: 600;
  color: #0f766e;
}
.chat-markdown :deep(code) {
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.85em;
  font-family: monospace;
}
.chat-markdown :deep(pre) {
  background: #f1f5f9;
  padding: 0.75rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 0.5rem 0;
}
.chat-markdown :deep(pre code) {
  background: none;
  padding: 0;
}
.chat-markdown :deep(hr) {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 0.75rem 0;
}
</style>
