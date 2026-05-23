/**
 * Minimal frontend Mock API server.
 * Supports the currently kept frontend pages: home, login, register, and error page.
 *
 * Start: node mock-server.js
 */

import http from 'node:http'

const PORT = 5000
const VERIFICATION_CODES = {}

const DEMO_USER = {
  id: 1,
  username: 'admin',
  role: 'admin',
  created_at: '2026-01-01T00:00:00',
}

const REGULAR_USER = {
  id: 2,
  username: 'zhangsan',
  role: 'publisher',
  created_at: '2026-03-15T00:00:00',
}

const REGISTERED_USERS = {}
let nextUserId = 3

const POSTERS = []

function jsonResponse(res, data, status = 200) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  })
  res.end(JSON.stringify(data))
}

function parseBody(req) {
  return new Promise((resolve) => {
    let body = ''
    req.on('data', (chunk) => { body += chunk })
    req.on('end', () => {
      try { resolve(JSON.parse(body)) }
      catch { resolve({}) }
    })
  })
}

function getToken(req) {
  const auth = req.headers.authorization || ''
  return auth.startsWith('Bearer ') ? auth.slice(7) : null
}

function findUser(usernameOrEmail) {
  const users = {
    admin: { password: 'admin123456', info: DEMO_USER },
    zhangsan: { password: '123456', info: REGULAR_USER },
    ...REGISTERED_USERS,
  }

  if (users[usernameOrEmail]) return users[usernameOrEmail]
  return Object.values(users).find((user) => user.info.email === usernameOrEmail) || null
}

const routes = {
  'GET /api/health': async () => ({
    status: 'ok',
    service: 'campus-activity-frontend-mock',
    timestamp: new Date().toISOString(),
  }),

  'POST /api/auth/login': async (req) => {
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

  'POST /api/auth/send-code': async (req) => {
    const { email } = await parseBody(req)
    if (!email || !String(email).includes('@')) {
      return { message: '请输入有效的邮箱地址' }
    }

    const code = String(Math.floor(100000 + Math.random() * 900000))
    VERIFICATION_CODES[email] = code
    console.log(`  [Mock] 验证码已发送到 ${email}: ${code}`)
    return { message: '验证码已发送', code }
  },

  'POST /api/auth/register': async (req) => {
    const { username, password, email, verification_code } = await parseBody(req)
    if (!username || !password) return { message: 'username and password are required' }
    if (String(username).length < 2 || String(username).length > 50) {
      return { message: 'username must be 2-50 characters' }
    }
    if (String(password).length < 6) return { message: 'password must be at least 6 characters' }
    if (findUser(username)) return { message: 'username already exists' }
    if (!email || !String(email).includes('@')) return { message: '请输入有效的邮箱地址' }
    if (!verification_code) return { message: '请输入验证码' }
    if (VERIFICATION_CODES[email] !== verification_code) return { message: '验证码错误或已过期' }

    delete VERIFICATION_CODES[email]
    const user = {
      id: nextUserId++,
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

  'GET /api/auth/me': async (req) => {
    if (!getToken(req)) return { user: null }
    return { user: DEMO_USER }
  },

  'GET /api/posters': async (req) => {
    const url = new URL(req.url, `http://localhost:${PORT}`)
    const page = Math.max(parseInt(url.searchParams.get('page') || '1', 10), 1)
    const perPage = Math.max(parseInt(url.searchParams.get('per_page') || '10', 10), 1)
    const status = url.searchParams.get('status')
    const keyword = url.searchParams.get('keyword') || url.searchParams.get('q')

    let items = [...POSTERS]
    if (status) items = items.filter((poster) => poster.status === status)
    if (keyword) {
      items = items.filter((poster) =>
        poster.title.includes(keyword)
        || poster.summary.includes(keyword)
        || poster.raw_text.includes(keyword)
        || poster.location.includes(keyword)
        || poster.organizer.includes(keyword),
      )
    }

    const total = items.length
    const start = (page - 1) * perPage
    return {
      items: items.slice(start, start + perPage),
      total,
      page,
      per_page: perPage,
      pages: Math.ceil(total / perPage),
    }
  },
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    })
    res.end()
    return
  }

  const method = req.method || 'GET'
  const pathname = (req.url || '/').split('?')[0]
  const key = `${method} ${pathname}`
  const handler = routes[key]

  if (!handler) {
    jsonResponse(res, { message: `Mock: ${key} not implemented` }, 404)
    return
  }

  try {
    const data = await handler(req)
    const status = data?.message === 'invalid credentials' ? 401 : 200
    jsonResponse(res, data, status)
  } catch (error) {
    jsonResponse(res, { message: error.message || 'mock server error' }, 500)
  }
})

server.listen(PORT, () => {
  console.log(`\n  Mock API server: http://localhost:${PORT}`)
  console.log('  Supported endpoints:')
  console.log('     GET  /api/health')
  console.log('     POST /api/auth/login (admin/admin123456, zhangsan/123456)')
  console.log('     POST /api/auth/register')
  console.log('     POST /api/auth/send-code')
  console.log('     GET  /api/auth/me')
  console.log('     GET  /api/posters')
  console.log('\n  Vite dev server: http://localhost:3000')
  console.log('  Run in another terminal: npm run dev\n')
})
