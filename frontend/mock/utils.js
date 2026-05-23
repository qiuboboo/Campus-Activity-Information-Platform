/**
 * Mock 共享工具函数
 */

import { DEMO_USER, REGULAR_USER, REGISTERED_USERS } from './db.js'

export function jsonResponse(res, data, status = 200) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  })
  res.end(JSON.stringify(data))
}

export function parseBody(req) {
  return new Promise((resolve) => {
    let body = ''
    req.on('data', (chunk) => { body += chunk })
    req.on('end', () => {
      try { resolve(JSON.parse(body)) }
      catch { resolve({}) }
    })
  })
}

export function getToken(req) {
  const auth = req.headers.authorization || ''
  return auth.startsWith('Bearer ') ? auth.slice(7) : null
}

export function findUser(usernameOrEmail) {
  const users = {
    admin: { password: 'admin123456', info: DEMO_USER },
    zhangsan: { password: '123456', info: REGULAR_USER },
    ...REGISTERED_USERS,
  }

  if (users[usernameOrEmail]) return users[usernameOrEmail]
  return Object.values(users).find((user) => user.info.email === usernameOrEmail) || null
}
