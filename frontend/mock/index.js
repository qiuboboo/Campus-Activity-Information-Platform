/**
 * Mock API 服务器入口
 *
 * 启动: node mock/index.js
 */

import http from 'node:http'
import { jsonResponse } from './utils.js'
import healthRoute from './routes/health.js'
import authRoutes from './routes/auth.js'
import posterRoutes from './routes/poster.js'
import calendarRoutes from './routes/calendar.js'

const PORT = 5000
const routes = {}

function registerRoute(routeDef) {
  const key = `${routeDef.method} ${routeDef.path}`
  routes[key] = routeDef.handler
}

registerRoute(healthRoute)
authRoutes.forEach(registerRoute)
posterRoutes.forEach(registerRoute)
calendarRoutes.forEach(registerRoute)

const server = http.createServer(async (req, res) => {
  // CORS 预检
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
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
  Object.keys(routes)
    .sort()
    .forEach((key) => console.log(`    ${key}`))
  console.log('\n  Vite dev server: http://localhost:3000')
  console.log('  Run in another terminal: npm run dev\n')
})
