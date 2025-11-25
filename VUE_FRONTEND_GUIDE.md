# Vue.js Frontend Implementation Guide

## Why Vue.js?

You mentioned preferring Vue over React - **excellent choice!** Vue.js is:

✅ **Easier to learn** than React
✅ **Better documentation** (official docs are outstanding)
✅ **More intuitive** (HTML-like templates)
✅ **Smaller bundle size** (~20KB vs React's 40KB)
✅ **Better TypeScript support** (native, not bolted on)
✅ **Composition API** (similar to React Hooks but cleaner)
✅ **Great ecosystem** (Vue Router, Pinia, Vite)

---

## Vue.js vs React Comparison

| Feature | Vue 3 | React |
|---------|-------|-------|
| **Learning Curve** | Easier (HTML templates) | Steeper (JSX) |
| **Bundle Size** | 20KB | 40KB |
| **TypeScript** | Native support | Requires extra setup |
| **State Management** | Pinia (simple) | Redux/Zustand (complex) |
| **Routing** | Vue Router (official) | React Router (3rd party) |
| **Documentation** | Excellent (official guide) | Good (community-driven) |
| **Performance** | Fast | Fast |
| **Job Market** | Growing | Larger |

**Verdict**: For this project, Vue.js is the better choice! 🎉

---

## Proposed Tech Stack

### Frontend (Vue.js 3)
```
Vue 3 + TypeScript + Vite + Pinia + Vue Router + Tailwind CSS
```

### Backend (Existing)
```
Flask (Admin API) + FastAPI (Public API)
```

### Architecture
```
┌─────────────────────────────────────┐
│     Vue 3 Frontend (Port 5173)      │
│  ┌───────────┐   ┌───────────────┐ │
│  │   Pages   │   │  Components   │ │
│  │           │   │               │ │
│  │ Dashboard │   │ MigrationList │ │
│  │ Login     │   │ StatsCard     │ │
│  │ Migrations│   │ Navbar        │ │
│  └───────────┘   └───────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  Pinia Stores (State)         │ │
│  │  - authStore                  │ │
│  │  - migrationStore             │ │
│  └───────────────────────────────┘ │
└───────────┬─────────────────────────┘
            │ HTTP Requests (Axios)
┌───────────▼─────────────────────────┐
│  Backend APIs                       │
│  ┌──────────────┐ ┌──────────────┐ │
│  │  Flask API   │ │ FastAPI API  │ │
│  │  (Port 5000) │ │ (Port 8000)  │ │
│  └──────────────┘ └──────────────┘ │
└─────────────────────────────────────┘
```

---

## Project Setup

### Step 1: Create Vue Project

```bash
# Navigate to your project directory
cd c:\Users\gag_a\Desktop\AI-Agent-MSSQL-DBT

# Create Vue 3 + TypeScript project
npm create vue@latest

# It will ask:
# Project name: frontend
# Add TypeScript? Yes
# Add JSX Support? No
# Add Vue Router? Yes
# Add Pinia? Yes
# Add Vitest? Yes
# Add ESLint? Yes
# Add Prettier? Yes
```

### Step 2: Project Structure

```
AI-Agent-MSSQL-DBT/
├── backend/               # Your existing Python code
│   ├── agents/
│   ├── app/
│   ├── flask_app/
│   └── fastapi_app/
├── frontend/              # New Vue.js frontend
│   ├── src/
│   │   ├── assets/        # Images, icons
│   │   ├── components/    # Reusable components
│   │   │   ├── MigrationCard.vue
│   │   │   ├── StatsCard.vue
│   │   │   ├── Navbar.vue
│   │   │   └── MigrationForm.vue
│   │   ├── views/         # Pages
│   │   │   ├── DashboardView.vue
│   │   │   ├── LoginView.vue
│   │   │   ├── MigrationsView.vue
│   │   │   └── UsersView.vue
│   │   ├── stores/        # Pinia stores
│   │   │   ├── auth.ts
│   │   │   └── migrations.ts
│   │   ├── router/        # Vue Router
│   │   │   └── index.ts
│   │   ├── types/         # TypeScript types
│   │   │   └── index.ts
│   │   ├── api/           # API client
│   │   │   └── client.ts
│   │   ├── App.vue        # Root component
│   │   └── main.ts        # Entry point
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── README.md
```

---

## Installation & Dependencies

### Install Vue Project

```bash
cd frontend
npm install
```

### Add Additional Dependencies

```bash
# Tailwind CSS (styling)
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Axios (HTTP client)
npm install axios

# VueUse (utility composables)
npm install @vueuse/core

# Headless UI (accessible components)
npm install @headlessui/vue

# Heroicons (icons)
npm install @heroicons/vue

# Chart.js (charts)
npm install chart.js vue-chartjs

# Date formatting
npm install dayjs
```

---

## TypeScript Types

### src/types/index.ts

```typescript
// User types
export interface User {
  id: number;
  email: string;
  is_admin: boolean;
  created_at: string;
}

// Migration types
export interface Migration {
  id: number;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  user_id: number;
  config?: MigrationConfig;
  error?: string;
}

export interface MigrationConfig {
  source_connection: string;
  target_project: string;
  tables?: string[];
}

// API Key types
export interface APIKey {
  id: number;
  name: string;
  key: string;
  is_active: boolean;
  rate_limit: number;
  created_at: string;
}

// Stats types
export interface DashboardStats {
  total_migrations: number;
  completed_migrations: number;
  running_migrations: number;
  failed_migrations: number;
  success_rate: number;
}

// API Response types
export interface APIResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

// Login types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}
```

---

## API Client

### src/api/client.ts

```typescript
import axios, { type AxiosInstance } from 'axios';
import type { User, Migration, APIKey, DashboardStats, LoginCredentials, LoginResponse } from '@/types';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API methods
export const authAPI = {
  login: (credentials: LoginCredentials) =>
    api.post<LoginResponse>('/auth/login', credentials),

  logout: () => api.post('/auth/logout'),

  getCurrentUser: () => api.get<User>('/auth/me'),
};

export const migrationsAPI = {
  getAll: () => api.get<Migration[]>('/migrations'),

  getOne: (id: number) => api.get<Migration>(`/migrations/${id}`),

  create: (data: Partial<Migration>) => api.post<Migration>('/migrations', data),

  delete: (id: number) => api.delete(`/migrations/${id}`),

  getProgress: (id: number) => api.get<{ progress: number }>(`/migrations/${id}/progress`),
};

export const statsAPI = {
  getDashboard: () => api.get<DashboardStats>('/stats/dashboard'),
};

export const apiKeysAPI = {
  getAll: () => api.get<APIKey[]>('/api-keys'),

  create: (name: string) => api.post<APIKey>('/api-keys', { name }),

  revoke: (id: number) => api.delete(`/api-keys/${id}`),
};

export default api;
```

---

## Pinia Stores

### src/stores/auth.ts

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authAPI } from '@/api/client';
import type { User, LoginCredentials } from '@/types';

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem('access_token'));
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Getters
  const isAuthenticated = computed(() => !!token.value);
  const isAdmin = computed(() => user.value?.is_admin ?? false);

  // Actions
  async function login(credentials: LoginCredentials) {
    loading.value = true;
    error.value = null;

    try {
      const response = await authAPI.login(credentials);
      token.value = response.data.access_token;
      user.value = response.data.user;
      localStorage.setItem('access_token', token.value);
      return true;
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Login failed';
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function logout() {
    try {
      await authAPI.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      token.value = null;
      user.value = null;
      localStorage.removeItem('access_token');
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return;

    try {
      const response = await authAPI.getCurrentUser();
      user.value = response.data;
    } catch (err) {
      // Token invalid, logout
      await logout();
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    fetchCurrentUser,
  };
});
```

### src/stores/migrations.ts

```typescript
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { migrationsAPI } from '@/api/client';
import type { Migration } from '@/types';

export const useMigrationsStore = defineStore('migrations', () => {
  // State
  const migrations = ref<Migration[]>([]);
  const currentMigration = ref<Migration | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Actions
  async function fetchMigrations() {
    loading.value = true;
    error.value = null;

    try {
      const response = await migrationsAPI.getAll();
      migrations.value = response.data;
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch migrations';
    } finally {
      loading.value = false;
    }
  }

  async function createMigration(data: Partial<Migration>) {
    loading.value = true;
    error.value = null;

    try {
      const response = await migrationsAPI.create(data);
      migrations.value.unshift(response.data);
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to create migration';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deleteMigration(id: number) {
    try {
      await migrationsAPI.delete(id);
      migrations.value = migrations.value.filter(m => m.id !== id);
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to delete migration';
      throw err;
    }
  }

  return {
    migrations,
    currentMigration,
    loading,
    error,
    fetchMigrations,
    createMigration,
    deleteMigration,
  };
});
```

---

## Vue Components

### src/components/StatsCard.vue

```vue
<script setup lang="ts">
interface Props {
  title: string;
  value: string | number;
  icon?: string;
  color?: 'blue' | 'green' | 'red' | 'yellow';
}

const props = withDefaults(defineProps<Props>(), {
  color: 'blue'
});

const colorClasses = {
  blue: 'text-blue-600 bg-blue-100',
  green: 'text-green-600 bg-green-100',
  red: 'text-red-600 bg-red-100',
  yellow: 'text-yellow-600 bg-yellow-100',
};
</script>

<template>
  <div class="bg-white overflow-hidden shadow rounded-lg">
    <div class="p-5">
      <div class="flex items-center">
        <div class="flex-shrink-0">
          <div :class="[colorClasses[color], 'rounded-md p-3']">
            <slot name="icon">
              <!-- Default icon -->
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </slot>
          </div>
        </div>
        <div class="ml-5 w-0 flex-1">
          <dt class="text-sm font-medium text-gray-500 truncate">
            {{ title }}
          </dt>
          <dd class="flex items-baseline">
            <div class="text-2xl font-semibold text-gray-900">
              {{ value }}
            </div>
          </dd>
        </div>
      </div>
    </div>
  </div>
</template>
```

### src/components/MigrationCard.vue

```vue
<script setup lang="ts">
import type { Migration } from '@/types';
import { computed } from 'vue';

interface Props {
  migration: Migration;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  delete: [id: number];
  view: [migration: Migration];
}>();

const statusColor = computed(() => {
  switch (props.migration.status) {
    case 'completed': return 'bg-green-100 text-green-800';
    case 'running': return 'bg-blue-100 text-blue-800';
    case 'failed': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
});

const statusIcon = computed(() => {
  switch (props.migration.status) {
    case 'completed': return '✓';
    case 'running': return '⏳';
    case 'failed': return '✗';
    default: return '⋯';
  }
});
</script>

<template>
  <div class="bg-white shadow rounded-lg p-6 hover:shadow-lg transition-shadow">
    <div class="flex items-center justify-between">
      <div class="flex-1">
        <div class="flex items-center space-x-3">
          <h3 class="text-lg font-semibold text-gray-900">
            {{ migration.name }}
          </h3>
          <span :class="[statusColor, 'px-2 py-1 text-xs font-medium rounded-full']">
            {{ statusIcon }} {{ migration.status }}
          </span>
        </div>
        <p class="mt-1 text-sm text-gray-500">
          Created {{ new Date(migration.created_at).toLocaleDateString() }}
        </p>
      </div>

      <div class="flex space-x-2">
        <button
          @click="emit('view', migration)"
          class="px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-800"
        >
          View
        </button>
        <button
          @click="emit('delete', migration.id)"
          class="px-3 py-2 text-sm font-medium text-red-600 hover:text-red-800"
        >
          Delete
        </button>
      </div>
    </div>

    <div v-if="migration.error" class="mt-3 p-3 bg-red-50 rounded-md">
      <p class="text-sm text-red-800">{{ migration.error }}</p>
    </div>
  </div>
</template>
```

---

## Vue Pages

### src/views/DashboardView.vue

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { statsAPI } from '@/api/client';
import StatsCard from '@/components/StatsCard.vue';
import type { DashboardStats } from '@/types';

const stats = ref<DashboardStats>({
  total_migrations: 0,
  completed_migrations: 0,
  running_migrations: 0,
  failed_migrations: 0,
  success_rate: 0,
});

const loading = ref(true);

onMounted(async () => {
  try {
    const response = await statsAPI.getDashboard();
    stats.value = response.data;
  } catch (error) {
    console.error('Failed to load stats:', error);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <StatsCard
        title="Total Migrations"
        :value="stats.total_migrations"
        color="blue"
      />

      <StatsCard
        title="Completed"
        :value="stats.completed_migrations"
        color="green"
      />

      <StatsCard
        title="Running"
        :value="stats.running_migrations"
        color="yellow"
      />

      <StatsCard
        title="Success Rate"
        :value="`${stats.success_rate}%`"
        color="blue"
      />
    </div>
  </div>
</template>
```

### src/views/LoginView.vue

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const email = ref('admin@test.com');
const password = ref('admin123');
const error = ref('');

async function handleLogin() {
  error.value = '';

  const success = await authStore.login({
    email: email.value,
    password: password.value,
  });

  if (success) {
    router.push('/');
  } else {
    error.value = authStore.error || 'Login failed';
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to your account
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          MSSQL to dbt Migration Platform
        </p>
      </div>

      <form class="mt-8 space-y-6" @submit.prevent="handleLogin">
        <div v-if="error" class="rounded-md bg-red-50 p-4">
          <p class="text-sm text-red-800">{{ error }}</p>
        </div>

        <div class="rounded-md shadow-sm -space-y-px">
          <div>
            <label for="email" class="sr-only">Email address</label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Email address"
            />
          </div>
          <div>
            <label for="password" class="sr-only">Password</label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Password"
            />
          </div>
        </div>

        <div>
          <button
            type="submit"
            :disabled="authStore.loading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <span v-if="authStore.loading">Signing in...</span>
            <span v-else>Sign in</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
```

---

## Running the Project

### Development Mode

**Terminal 1 - Backend (Flask):**
```bash
cd c:\Users\gag_a\Desktop\AI-Agent-MSSQL-DBT
python run_flask.py
# Runs on http://localhost:5000
```

**Terminal 2 - Backend (FastAPI):**
```bash
cd c:\Users\gag_a\Desktop\AI-Agent-MSSQL-DBT
python run_fastapi.py
# Runs on http://localhost:8000
```

**Terminal 3 - Frontend (Vue):**
```bash
cd c:\Users\gag_a\Desktop\AI-Agent-MSSQL-DBT\frontend
npm run dev
# Runs on http://localhost:5173
```

---

## Environment Variables

### frontend/.env

```env
# API URL
VITE_API_URL=http://localhost:8000/api/v1

# Flask URL (if needed)
VITE_FLASK_URL=http://localhost:5000
```

---

## Implementation Timeline

### Week 1: Setup & Basic Pages
- **Day 1-2**: Project setup, dependencies
- **Day 3-4**: Login page, authentication
- **Day 5**: Dashboard with stats

### Week 2: Main Features
- **Day 6-7**: Migrations list and create
- **Day 8-9**: Migration details and progress
- **Day 10**: User management (admin)

### Week 3: Polish & Deploy
- **Day 11-12**: Charts, notifications, polish UI
- **Day 13-14**: Testing, bug fixes
- **Day 15**: Build and deploy

---

## Want me to implement this?

I can help you build the Vue.js frontend step by step! Just say:

1. **"Set up Vue project"** - I'll guide you through initial setup
2. **"Build login page"** - I'll create the authentication flow
3. **"Build dashboard"** - I'll create the dashboard with stats
4. **"Build migrations page"** - I'll create full migration management

**Ready to start?** 🚀
