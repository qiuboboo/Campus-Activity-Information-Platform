import { createRouter, createWebHistory } from 'vue-router'
import type { UserRole } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: UserRole[]
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Home', component: () => import('@/views/home/HomeView.vue') },
    { path: '/search', name: 'Search', component: () => import('@/views/search/SearchView.vue') },
    { path: '/activities', name: 'Activities', component: () => import('@/views/activity/ActivityListView.vue') },
    { path: '/activity/:id', name: 'ActivityDetail', component: () => import('@/views/activity/ActivityDetail.vue') },
    { path: '/about', name: 'About', component: () => import('@/views/info/AboutView.vue') },
    { path: '/contact', name: 'Contact', component: () => import('@/views/info/ContactView.vue') },
    { path: '/auth/login', name: 'Login', component: () => import('@/views/auth/login/LoginView.vue') },
    { path: '/auth/register', name: 'Register', component: () => import('@/views/auth/register/RegisterView.vue') },
    { path: '/auth/forgot-password', name: 'ForgotPassword', component: () => import('@/views/auth/forgot-password/ForgotPasswordView.vue') },
    { path: '/profile', name: 'Profile', component: () => import('@/views/profile/ProfileView.vue'), meta: { requiresAuth: true } },
    { path: '/calendar', name: 'Calendar', component: () => import('@/views/calendar/CalendarView.vue'), meta: { requiresAuth: true } },
    { path: '/my/activities', name: 'MyActivities', component: () => import('@/views/activity/MyActivitiesView.vue'), meta: { requiresAuth: true, roles: ['publisher', 'admin'] } },
    { path: '/activities/create', name: 'ActivityCreate', component: () => import('@/views/activity/ActivityEditorView.vue'), meta: { requiresAuth: true, roles: ['publisher', 'admin'] } },
    { path: '/activities/:id/edit', name: 'ActivityEdit', component: () => import('@/views/activity/ActivityEditorView.vue'), meta: { requiresAuth: true, roles: ['publisher', 'admin'] } },
    { path: '/admin', name: 'Admin', component: () => import('@/views/admin/AdminDashboardView.vue'), meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/admin/review', name: 'AdminReview', component: () => import('@/views/admin/ReviewView.vue'), meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/admin/data-sources', name: 'DataSources', component: () => import('@/views/admin/DataSourcesView.vue'), meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/admin/knowledge', name: 'AdminKnowledge', component: () => import('@/views/admin/KnowledgeAdminView.vue'), meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/admin/ai-config', name: 'AdminAiConfig', component: () => import('@/views/admin/AiConfigView.vue'), meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/admin/dicts', name: 'AdminDicts', component: () => import('@/views/admin/DictsView.vue'), meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/admin/audit-logs', name: 'AuditLogs', component: () => import('@/views/admin/AuditLogsView.vue'), meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/forbidden', name: 'Forbidden', component: () => import('@/views/error/ForbiddenView.vue') },
    { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/error/NotFound.vue') },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.initialize()
  const publicAuthPages = ['/auth/login', '/auth/register']
  if (auth.isLoggedIn && publicAuthPages.includes(to.path)) return '/'
  if (to.meta.requiresAuth && !auth.isLoggedIn) return { path: '/auth/login', query: { redirect: to.fullPath } }
  if (to.meta.roles && (!auth.user || !to.meta.roles.includes(auth.user.role))) return { path: '/forbidden' }
  return true
})

export default router
