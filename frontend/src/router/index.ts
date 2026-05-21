import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue'),
    },
    {
      path: '/',
      component: () => import('@/components/AppLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
        },
        {
          path: 'posters',
          name: 'PosterList',
          component: () => import('@/views/posters/PosterList.vue'),
        },
        {
          path: 'posters/create',
          name: 'PosterCreate',
          component: () => import('@/views/posters/PosterCreate.vue'),
        },
        {
          path: 'posters/:id',
          name: 'PosterDetail',
          component: () => import('@/views/posters/PosterDetail.vue'),
        },
        {
          path: 'posters/review',
          name: 'PosterReview',
          component: () => import('@/views/posters/PosterReview.vue'),
          meta: { role: 'admin' },
        },
        {
          path: 'knowledge',
          name: 'KnowledgeNodes',
          component: () => import('@/views/knowledge/KnowledgeNodes.vue'),
        },
        {
          path: 'knowledge/:id',
          name: 'KnowledgeNodeDetail',
          component: () => import('@/views/knowledge/KnowledgeNodeDetail.vue'),
        },
        {
          path: 'datasources',
          name: 'DataSourceList',
          component: () => import('@/views/datasources/DataSourceList.vue'),
          meta: { role: 'admin' },
        },
        {
          path: 'search',
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
  if (to.path !== '/login' && !auth.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && auth.isLoggedIn) {
    next('/dashboard')
  } else if (to.meta?.role === 'admin' && !auth.isAdmin) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
