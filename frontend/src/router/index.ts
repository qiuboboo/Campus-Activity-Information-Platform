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
      path: '/auth/login',
      name: 'Login',
      component: () => import('@/views/auth/login/LoginView.vue'),
    },
    {
      path: '/auth/register',
      name: 'Register',
      component: () => import('@/views/auth/register/RegisterView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/error/NotFound.vue'),
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  const publicPages = ['/auth/login', '/auth/register']
  const requiresAuth = to.meta?.requiresAuth === true

  if (auth.isLoggedIn && publicPages.includes(to.path)) {
    next('/')
    return
  }

  if (!auth.isLoggedIn && requiresAuth) {
    next({ path: '/auth/login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

export default router
