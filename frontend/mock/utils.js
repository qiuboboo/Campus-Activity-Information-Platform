/**
 * Mock 共享工具函数
 */

import { DEMO_USER, REGULAR_USER, REGISTERED_USERS, SESSIONS } from './db.js'
import { Readable } from 'node:stream'

export function jsonResponse(res, data, status = 200) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
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

export async function parseMultipartFile(req) {
  const contentType = req.headers['content-type'] || ''
  if (!contentType.startsWith('multipart/form-data')) return null
  const request = new Request('http://mock.local', {
    method: req.method,
    headers: req.headers,
    body: Readable.toWeb(req),
    duplex: 'half',
  })
  const form = await request.formData()
  const file = form.get('file')
  if (!file || typeof file === 'string' || typeof file.arrayBuffer !== 'function') return null
  return {
    name: file.name,
    type: file.type || 'application/octet-stream',
    size: file.size,
    buffer: Buffer.from(await file.arrayBuffer()),
  }
}

export function rawResponse(res, body, status = 200, contentType = 'application/octet-stream', headers = {}) {
  res.writeHead(status, {
    'Content-Type': contentType,
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Expose-Headers': 'X-Captcha-Token',
    ...headers,
  })
  res.end(body)
}

export function getCurrentUser(req) {
  const token = getToken(req)
  if (!token) return null
  const username = SESSIONS[token]
  return findUser(username)?.info || null
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
