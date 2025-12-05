import { createRouter, createWebHistory, type RouteRecordRaw, type NavigationGuardNext, type RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Views
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import DashboardView from '@/views/DashboardView.vue'
import MigrationsView from '@/views/MigrationsView.vue'
import LandingView from '@/views/LandingView.vue'

// Lazy-loaded views
const MigrationDetailView = () => import('@/views/MigrationDetailView.vue')
const NewMigrationView = () => import('@/views/NewMigrationView.vue')
const ProfileView = () => import('@/views/ProfileView.vue')
const SettingsView = () => import('@/views/SettingsView.vue')
const DocumentationView = () => import('@/views/DocumentationView.vue')
const NotFoundView = () => import('@/views/NotFoundView.vue')
const ForgotPasswordView = () => import('@/views/ForgotPasswordView.vue')
const ResetPasswordView = () => import('@/views/ResetPasswordView.vue')
const DataPrepAgentView = () => import('@/views/DataPrepAgentView.vue')
const MLFineTuningView = () => import('@/views/MLFineTuningView.vue')
const AgentsView = () => import('@/views/AgentsView.vue')

// Route definitions
const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Landing',
    component: LandingView,
    meta: {
      requiresAuth: false,
      title: 'DataMigrate AI - AI-Powered Database Migrations'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: {
      requiresAuth: false,
      title: 'Login - DataMigrate AI',
      guestOnly: true // Redirect to dashboard if already logged in
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: {
      requiresAuth: false,
      title: 'Register - DataMigrate AI',
      guestOnly: true // Redirect to dashboard if already logged in
    }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPasswordView,
    meta: {
      requiresAuth: false,
      title: 'Forgot Password - DataMigrate AI',
      guestOnly: true
    }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: ResetPasswordView,
    meta: {
      requiresAuth: false,
      title: 'Reset Password - DataMigrate AI',
      guestOnly: true
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: {
      requiresAuth: true,
      title: 'Dashboard - DataMigrate AI'
    }
  },
  {
    path: '/migrations',
    name: 'Migrations',
    component: MigrationsView,
    meta: {
      requiresAuth: true,
      title: 'Migrations - DataMigrate AI'
    }
  },
  {
    path: '/migrations/new',
    name: 'NewMigration',
    component: NewMigrationView,
    meta: {
      requiresAuth: true,
      title: 'New Migration - DataMigrate AI'
    }
  },
  {
    path: '/migrations/:id',
    name: 'MigrationDetail',
    component: MigrationDetailView,
    meta: {
      requiresAuth: true,
      title: 'Migration Detail - DataMigrate AI'
    },
    props: true
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    meta: {
      requiresAuth: true,
      title: 'Profile - DataMigrate AI'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsView,
    meta: {
      requiresAuth: true,
      title: 'Settings - DataMigrate AI'
    }
  },
  {
    path: '/docs',
    name: 'Documentation',
    component: DocumentationView,
    meta: {
      requiresAuth: true,
      title: 'Documentation - DataMigrate AI'
    }
  },
  {
    path: '/agents',
    name: 'Agents',
    component: AgentsView,
    meta: {
      requiresAuth: true,
      title: 'AI Agents - DataMigrate AI'
    }
  },
  {
    path: '/agents/dataprep',
    name: 'DataPrepAgent',
    component: DataPrepAgentView,
    meta: {
      requiresAuth: true,
      title: 'DataPrep AI Agent - DataMigrate AI'
    }
  },
  {
    path: '/agents/ml-finetuning',
    name: 'MLFineTuning',
    component: MLFineTuningView,
    meta: {
      requiresAuth: true,
      title: 'ML Fine-Tuning Agent - DataMigrate AI'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFoundView,
    meta: {
      requiresAuth: false,
      title: '404 Not Found - DataMigrate AI'
    }
  }
]

// Create router instance
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Scroll to saved position on back/forward navigation
    if (savedPosition) {
      return savedPosition
    }
    // Scroll to top on new page navigation
    return { top: 0 }
  }
})

// Global navigation guard for authentication
router.beforeEach(async (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  const authStore = useAuthStore()

  // Set page title
  if (to.meta.title) {
    document.title = to.meta.title as string
  }

  // Check if route requires authentication
  const requiresAuth = to.meta.requiresAuth as boolean
  const guestOnly = to.meta.guestOnly as boolean
  const isAuthenticated = authStore.isAuthenticated

  // Initialize auth store if not already initialized
  if (!authStore.initialized) {
    try {
      await authStore.initialize()
    } catch (error) {
      console.error('Failed to initialize auth:', error)
    }
  }

  // Handle guest-only routes (like login page)
  if (guestOnly && isAuthenticated) {
    console.log('User already authenticated, redirecting to dashboard')
    return next({ name: 'Dashboard' })
  }

  // Handle protected routes
  if (requiresAuth && !isAuthenticated) {
    console.log('Route requires authentication, redirecting to login')
    return next({
      name: 'Login',
      query: { redirect: to.fullPath } // Save intended destination
    })
  }

  // Allow navigation
  next()
})

// Global after navigation hook
router.afterEach((to, from) => {
  // Log navigation for debugging
  if (import.meta.env.DEV) {
    console.log(`Navigated from ${from.path} to ${to.path}`)
  }

  // Close any open modals or menus
  // You can emit events here if needed
})

// Error handler
router.onError((error) => {
  console.error('Router error:', error)

  // Handle chunk loading errors (lazy-loaded components)
  if (error.message.includes('Failed to fetch dynamically imported module')) {
    console.warn('Chunk loading failed, reloading page')
    window.location.reload()
  }
})

export default router
