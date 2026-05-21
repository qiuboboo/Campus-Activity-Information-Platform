import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/home/HomeView.vue'),
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue'),
    },
    {
      path: '/dashboard',
      component: () => import('@/components/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
        },
      ],
    },
    {
      path: '/posters',
      component: () => import('@/components/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'PosterList',
          component: () => import('@/views/posters/PosterList.vue'),
        },
        {
          path: 'create',
          name: 'PosterCreate',
          component: () => import('@/views/posters/PosterCreate.vue'),
        },
        {
          path: 'review',
          name: 'PosterReview',
          component: () => import('@/views/posters/PosterReview.vue'),
          meta: { role: 'admin' },
        },
        {
          path: ':id',
          name: 'PosterDetail',
          component: () => import('@/views/posters/PosterDetail.vue'),
        },
        {
          path: ':id/edit',
          name: 'PosterEdit',
          component: () => import('@/views/posters/PosterEdit.vue'),
        },
      ],
    },
    {
      path: '/knowledge',
      component: () => import('@/components/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'KnowledgeNodes',
          component: () => import('@/views/knowledge/KnowledgeNodes.vue'),
        },
        {
          path: ':id',
          name: 'KnowledgeNodeDetail',
          component: () => import('@/views/knowledge/KnowledgeNodeDetail.vue'),
        },
      ],
    },
    {
      path: '/datasources',
      component: () => import('@/components/AppLayout.vue'),
      meta: { role: 'admin' },
      children: [
        {
          path: '',
          name: 'DataSourceList',
          component: () => import('@/views/datasources/DataSourceList.vue'),
        },
        {
          path: 'create',
          name: 'DataSourceCreate',
          component: () => import('@/views/datasources/DataSourceForm.vue'),
        },
        {
          path: ':id/edit',
          name: 'DataSourceEdit',
          component: () => import('@/views/datasources/DataSourceForm.vue'),
        },
      ],
    },
    {
      path: '/audit-logs',
      component: () => import('@/components/AppLayout.vue'),
      meta: { role: 'admin' },
      children: [
        {
          path: '',
          name: 'AuditLogs',
          component: () => import('@/views/audit/AuditLogs.vue'),
        },
      ],
    },
    {
      path: '/search',
      component: () => import('@/components/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'SearchView',
          component: () => import('@/views/search/SearchView.vue'),
        },
      ],
    },
  ],
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  const publicPages = ['/', '/login']
  if (publicPages.includes(to.path)) {
    next()
  } else if (!auth.isLoggedIn) {
    next('/login')
  } else if (to.meta?.role === 'admin' && !auth.isAdmin) {
    next('/')
  } else {
    next()
  }
})

export default router
