/**
 * 认证相关 Mock 路由
 *   POST /api/auth/login
 *   POST /api/auth/send-code
 *   POST /api/auth/register
 *   GET  /api/auth/me
 */

import { parseBody, getToken, findUser } from '../utils.js'
import {
  DEMO_USER,
  REGISTERED_USERS,
  VERIFICATION_CODES,
  getNextUserId,
} from '../db.js'

export default [
  {
    method: 'POST',
    path: '/api/auth/login',
    handler: async (req) => {
      const { username, password } = await parseBody(req)
      const matched = findUser(username)
      if (matched && matched.password === password) {
        return {
          token: `mock-jwt-token-${Date.now()}`,
          user: matched.info,
        }
      }
      return { message: 'invalid credentials' }
    },
  },
  {
    method: 'POST',
    path: '/api/auth/send-code',
    handler: async (req) => {
      const { email } = await parseBody(req)
      if (!email || !String(email).includes('@')) {
        return { message: '请输入有效的邮箱地址' }
      }

      const code = String(Math.floor(100000 + Math.random() * 900000))
      VERIFICATION_CODES[email] = code
      console.log(`  [Mock] 验证码已发送到 ${email}: ${code}`)
      return { message: '验证码已发送', code }
    },
  },
  {
    method: 'POST',
    path: '/api/auth/register',
    handler: async (req) => {
      const { username, password, email, verification_code } = await parseBody(req)

      if (!username || !password) return { message: 'username and password are required' }
      if (String(username).length < 2 || String(username).length > 50) {
        return { message: 'username must be 2-50 characters' }
      }
      if (String(password).length < 6) return { message: 'password must be at least 6 characters' }
      if (findUser(username)) return { message: 'username already exists' }
      if (!email || !String(email).includes('@')) return { message: '请输入有效的邮箱地址' }
      if (!verification_code) return { message: '请输入验证码' }
      if (VERIFICATION_CODES[email] !== verification_code) {
        return { message: '验证码错误或已过期' }
      }

      delete VERIFICATION_CODES[email]
      const user = {
        id: getNextUserId(),
        username,
        role: 'viewer',
        email,
        created_at: new Date().toISOString(),
      }
      REGISTERED_USERS[username] = { password, info: user }

      return {
        token: `mock-jwt-token-${Date.now()}`,
        user,
      }
    },
  },
  {
    method: 'GET',
    path: '/api/auth/me',
    handler: async (req) => {
      if (!getToken(req)) return { user: null }
      return { user: DEMO_USER }
    },
  },
]
