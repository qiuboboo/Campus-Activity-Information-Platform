/**
 * 认证相关 Mock 路由
 *   GET  /api/auth/captcha
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

// In-memory captcha store: token → code
const CAPTCHA_STORE = {}

function generateCaptchaCode() {
  return String(Math.floor(1000 + Math.random() * 9000))
}

function captchaSvg(code) {
  const chars = code.split('')
  const colors = ['#e74c3c', '#2ecc71', '#3498db', '#f39c12']
  const items = chars.map((ch, i) => {
    const x = 30 + i * 28
    const y = 32 + (Math.random() * 12 - 6)
    const rotate = (Math.random() * 30 - 15).toFixed(1)
    const color = colors[i % colors.length]
    const size = 22 + Math.floor(Math.random() * 8)
    return `<text x="${x}" y="${y}" transform="rotate(${rotate} ${x} ${y})" fill="${color}" font-size="${size}" font-family="Arial,sans-serif" font-weight="bold">${ch}</text>`
  }).join('')
  // Add noise lines
  const lines = Array.from({ length: 6 }, () => {
    const x1 = Math.floor(Math.random() * 150)
    const y1 = Math.floor(Math.random() * 50)
    const x2 = x1 + Math.floor(Math.random() * 30 - 15)
    const y2 = y1 + Math.floor(Math.random() * 30 - 15)
    return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#ddd" stroke-width="1"/>`
  }).join('')
  return `<svg xmlns="http://www.w3.org/2000/svg" width="140" height="50" viewBox="0 0 140 50" style="background:#f9f9f9">${lines}${items}</svg>`
}

export default [
  {
    method: 'GET',
    path: '/api/auth/captcha',
    handler: async (_req, res) => {
      const code = generateCaptchaCode()
      const token = `captcha-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
      CAPTCHA_STORE[token] = code
      // Expire after 5 minutes
      setTimeout(() => delete CAPTCHA_STORE[token], 300_000)

      res.writeHead(200, {
        'Content-Type': 'image/svg+xml',
        'X-Captcha-Token': token,
        'Cache-Control': 'no-store',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Expose-Headers': 'X-Captcha-Token',
      })
      res.end(captchaSvg(code))
      return null // signal raw response already written
    },
  },
  {
    method: 'POST',
    path: '/api/auth/login',
    handler: async (req) => {
      const { username, password, captcha_token, captcha_code } = await parseBody(req)

      // Validate captcha
      if (!captcha_token || !captcha_code) {
        return { message: '请输入验证码' }
      }
      const stored = CAPTCHA_STORE[captcha_token]
      if (!stored || stored !== captcha_code) {
        delete CAPTCHA_STORE[captcha_token]
        return { message: '验证码错误或已过期，请刷新后重试' }
      }
      delete CAPTCHA_STORE[captcha_token]

      const matched = findUser(username)
      if (matched && matched.password === password) {
        return {
          token: `mock-jwt-token-${Date.now()}`,
          user: matched.info,
        }
      }
      return { message: '用户名或密码错误' }
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
