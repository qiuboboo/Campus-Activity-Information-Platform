/**
 * 认证相关 Mock 路由
 *   POST /api/auth/login
 *   POST /api/auth/send-code
 *   POST /api/auth/register
 *   GET  /api/auth/me
 */

import { parseBody, getCurrentUser, findUser } from '../utils.js'
import {
  DEMO_USER,
  REGISTERED_USERS,
  SESSIONS,
  CAPTCHA_CODES,
  VERIFICATION_CODES,
  getNextUserId,
} from '../db.js'

export default [
  {
    method: 'GET',
    path: '/api/auth/captcha',
    handler: async () => {
      const token = `captcha-${Date.now()}-${Math.random().toString(36).slice(2)}`
      const code = String(Math.floor(1000 + Math.random() * 9000))
      CAPTCHA_CODES[token] = code
      const image = `<svg xmlns="http://www.w3.org/2000/svg" width="116" height="38" viewBox="0 0 116 38"><rect width="116" height="38" fill="#eef7f1"/><path d="M0 9L116 25M4 34L99 3" stroke="#b7d9c6"/><text x="58" y="27" text-anchor="middle" font-family="monospace" font-size="22" letter-spacing="4" fill="#0d5e3c">${code}</text></svg>`
      return { __raw: image, __contentType: 'image/svg+xml; charset=utf-8', __headers: { 'X-Captcha-Token': token } }
    },
  },
  {
    method: 'POST',
    path: '/api/auth/login',
    handler: async (req) => {
      const { username, password, captcha_token, captcha_code } = await parseBody(req)
      if (!verifyCaptcha(captcha_token, captcha_code)) return { __status: 422, message: '图形验证码错误或已过期' }
      const matched = findUser(username)
      if (matched && matched.password === password) {
        return {
          token: issueToken(matched.info.username),
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
      const { username, password, email, verification_code, captcha_token, captcha_code } = await parseBody(req)

      if (!verifyCaptcha(captcha_token, captcha_code)) return { __status: 422, message: '图形验证码错误或已过期' }

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
        token: issueToken(username),
        user,
      }
    },
  },
  {
    method: 'GET',
    path: '/api/auth/me',
    handler: async (req) => {
      return { user: getCurrentUser(req) }
    },
  },
  {
    method: 'PATCH',
    path: '/api/auth/me',
    handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '登录已过期' }
      const { display_name, email } = await parseBody(req)
      if (display_name) user.display_name = display_name
      if (email) user.email = email
      return { user }
    },
  },
  {
    method: 'POST',
    path: '/api/auth/forgot-password',
    handler: async (req) => {
      const { email } = await parseBody(req)
      if (!email || !String(email).includes('@')) return { __status: 422, message: '请输入有效的邮箱地址' }
      return { message: '重置说明已发送' }
    },
  },
]

function issueToken(username) {
  const token = `mock-jwt-${Date.now()}-${Math.random().toString(36).slice(2)}`
  SESSIONS[token] = username
  return token
}

function verifyCaptcha(token, code) {
  if (!token || !code || CAPTCHA_CODES[token] !== String(code)) return false
  delete CAPTCHA_CODES[token]
  return true
}
