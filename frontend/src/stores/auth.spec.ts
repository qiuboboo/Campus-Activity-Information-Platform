import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from './auth'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  getMe: vi.fn(),
}))

import { getMe, login } from '@/api/auth'

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('persists a successful login and clears it on logout', async () => {
    vi.mocked(login).mockResolvedValue({ data: { token: 'test-token', user: { id: 2, username: 'zhangsan', role: 'publisher', created_at: '2026-01-01T00:00:00' } } } as any)
    const auth = useAuthStore()
    await auth.login('zhangsan', '123456', { token: 'captcha-token', code: '1234' })
    expect(auth.isLoggedIn).toBe(true)
    expect(auth.isPublisher).toBe(true)
    expect(localStorage.getItem('token')).toBe('test-token')
    auth.logout()
    expect(auth.isLoggedIn).toBe(false)
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('always settles the startup state when persisted authentication cannot be verified', async () => {
    localStorage.setItem('token', 'expired-token')
    localStorage.setItem('user', JSON.stringify({ id: 2, username: 'zhangsan', role: 'publisher', created_at: '2026-01-01T00:00:00' }))
    vi.mocked(getMe).mockRejectedValue(new Error('network timeout'))
    const auth = useAuthStore()
    await auth.initialize()
    expect(auth.ready).toBe(true)
    expect(auth.isLoggedIn).toBe(false)
  })
})
