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
  const authPages = ['/auth/login', '/auth/register']

  if (auth.isLoggedIn && authPages.includes(to.path)) {
    next('/')
    return
  }

  next()
})

export default router
