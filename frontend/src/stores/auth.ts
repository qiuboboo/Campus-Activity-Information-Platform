import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe } from '@/api/auth'
import type { UserProfile } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  // 启动时清理 localStorage 中可能残留的坏数据
  ;['token', 'user', 'remembered_user'].forEach(key => {
    try {
      const val = localStorage.getItem(key)
      if (val === 'undefined' || val === 'null' || val === undefined) {
        localStorage.removeItem(key)
      } else if (key === 'user' && val) {
        JSON.parse(val)
      }
    } catch {
      localStorage.removeItem(key)
    }
  })

  const token = ref(localStorage.getItem('token') || '')
  const user = ref<UserProfile | null>(
    JSON.parse(localStorage.getItem('user') || 'null'),
  )
  const ready = ref(false)
  let initializePromise: Promise<void> | null = null

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isPublisher = computed(() => user.value?.role === 'publisher' || user.value?.role === 'admin')

  async function login(username: string, password: string, captcha: { token: string; code: string }) {
    const res = await loginApi({ username, password, captcha_token: captcha.token, captcha_code: captcha.code })
    const data = res.data
    if (!data.token) {
      throw new Error(data.message || 'invalid credentials')
    }
    token.value = data.token
    user.value = data.user
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    return data
  }

  async function initialize() {
    if (ready.value) return
    if (initializePromise) return initializePromise
    initializePromise = (async () => {
      try {
        if (!token.value) return
        const { data } = await getMe()
        const currentUser = data && typeof data === 'object' && 'user' in data ? data.user : data
        if (!currentUser) throw new Error('session expired')
        user.value = currentUser
        localStorage.setItem('user', JSON.stringify(currentUser))
      } catch {
        logout()
      } finally {
        ready.value = true
      }
    })()
    return initializePromise
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, ready, isLoggedIn, isAdmin, isPublisher, login, logout, initialize }
})
