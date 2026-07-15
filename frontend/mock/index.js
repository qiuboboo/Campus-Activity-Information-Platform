/**
 * Mock API 服务器入口
 *
 * 启动: node mock/index.js
 */

import http from 'node:http'
import { jsonResponse, rawResponse } from './utils.js'
import healthRoute from './routes/health.js'
import authRoutes from './routes/auth.js'
import activityRoutes from './routes/activity.js'
import calendarRoutes from './routes/calendar.js'
import profileRoutes from './routes/profile.js'
import adminRoutes from './routes/admin.js'
import knowledgeRoutes from './routes/knowledge.js'
import uploadRoutes from './routes/upload.js'

const PORT = 5000
const routes = {}

function registerRoute(routeDef) {
  const key = `${routeDef.method} ${routeDef.path}`
  routes[key] = routeDef.handler
}

function matchRoute(method, pathname) {
  const exactKey = `${method} ${pathname}`
  if (routes[exactKey]) {
    return { handler: routes[exactKey], params: {} }
  }

  for (const [key, handler] of Object.entries(routes)) {
    const [routeMethod, routePath] = key.split(' ')
    if (routeMethod !== method) continue

    const routeParts = routePath.split('/').filter(Boolean)
    const pathParts = pathname.split('/').filter(Boolean)
    if (routeParts.length !== pathParts.length) continue

    const params = {}
    let matched = true

    for (let i = 0; i < routeParts.length; i++) {
      const routePart = routeParts[i]
      const pathPart = pathParts[i]

      if (routePart.startsWith(':')) {
        params[routePart.slice(1)] = decodeURIComponent(pathPart)
        continue
      }

      if (routePart !== pathPart) {
        matched = false
        break
      }
    }

    if (matched) {
      return { handler, params }
    }
  }

  return null
}

registerRoute(healthRoute)
authRoutes.forEach(registerRoute)
activityRoutes.forEach(registerRoute)
calendarRoutes.forEach(registerRoute)
profileRoutes.forEach(registerRoute)
adminRoutes.forEach(registerRoute)
  knowledgeRoutes.forEach(registerRoute)
  uploadRoutes.forEach(registerRoute)

const server = http.createServer(async (req, res) => {
  // CORS 预检
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    })
    res.end()
    return
  }

  const method = req.method || 'GET'
  const pathname = (req.url || '/').split('?')[0]
  const matchedRoute = matchRoute(method, pathname)
  const key = `${method} ${pathname}`
  const handler = matchedRoute?.handler

  if (!handler) {
    jsonResponse(res, { message: `Mock: ${key} not implemented` }, 404)
    return
  }

  try {
    req.params = matchedRoute?.params || {}
    const data = await handler(req)
    if (data?.__raw) {
      rawResponse(res, data.__raw, data.__status || 200, data.__contentType, data.__headers)
      return
    }
    const status = data?.__status || (data?.message === 'invalid credentials' ? 401 : 200)
    if (data && typeof data === 'object' && '__status' in data) {
      const { __status, ...payload } = data
      jsonResponse(res, payload, status)
      return
    }
    jsonResponse(res, data, status)
  } catch (error) {
    jsonResponse(res, { message: error.message || 'mock server error' }, 500)
  }
})

server.listen(PORT, () => {
  console.log(`\n  Mock API server: http://localhost:${PORT}`)
  console.log('  Supported endpoints:')
  Object.keys(routes)
    .sort()
    .forEach((key) => console.log(`    ${key}`))
  console.log('\n  Vite dev server: http://localhost:3000')
  console.log('  Run in another terminal: npm run dev\n')
})
