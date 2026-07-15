import { ACTIVITIES, USER_STATE } from '../db.js'
import { getCurrentUser, parseBody } from '../utils.js'

function nodesFor(activity) {
  return [
    activity.location && { id: 1000 + activity.id, name: activity.location, node_type: 'place' },
    activity.organizer && { id: 2000 + activity.id, name: activity.organizer, node_type: 'organization' },
    activity.activity_type && { id: 3000 + activity.id, name: activity.activity_type, node_type: 'topic' },
  ].filter(Boolean)
}

export default [
  {
    method: 'GET', path: '/api/posters/:id/related', handler: async (req) => {
      const activity = ACTIVITIES.find((item) => item.id === Number(req.params.id) && item.status === 'published')
      if (!activity) return { __status: 404, message: 'activity not found' }
      const related = ACTIVITIES
        .filter((item) => item.id !== activity.id && item.status === 'published' && (item.activity_type === activity.activity_type || item.organizer === activity.organizer))
        .slice(0, 4)
        .map((item) => ({ activity: item, reason: item.activity_type === activity.activity_type ? `同属${activity.activity_type || '相关'}活动` : '主办方相同' }))
      return { nodes: nodesFor(activity), related, source: { name: activity.source_name || activity.organizer, url: activity.source_url || 'https://www.sysu.edu.cn' } }
    },
  },
  {
    method: 'GET', path: '/api/knowledge/nodes', handler: async (req) => {
      const url = new URL(req.url, 'http://localhost:5000')
      const q = url.searchParams.get('q') || ''
      const type = url.searchParams.get('node_type') || ''
      const unique = new Map()
      ACTIVITIES.filter((item) => item.status === 'published').flatMap(nodesFor).forEach((node) => unique.set(`${node.node_type}:${node.name}`, node))
      const items = [...unique.values()].filter((node) => (!q || node.name.includes(q)) && (!type || node.node_type === type))
      return { items }
    },
  },
  {
    method: 'POST', path: '/api/subscriptions', handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '请先登录' }
      const { node_id, keyword } = await parseBody(req)
      const nodeId = Number(node_id)
      const node = ACTIVITIES.flatMap(nodesFor).find((item) => item.id === nodeId)
      if (!node && !String(keyword || '').trim()) return { __status: 422, message: '请输入订阅关键词或选择知识节点' }
      const items = USER_STATE.subscriptions[user.id] ||= []
      const exists = items.find((item) => node ? item.node_id === node.id : item.keyword === String(keyword).trim())
      if (exists) return exists
      const subscription = { id: Date.now(), ...(node ? { node_id: node.id } : {}), keyword: node?.name || String(keyword).trim(), created_at: new Date().toISOString() }
      items.push(subscription)
      return subscription
    },
  },
  {
    method: 'GET', path: '/api/subscriptions', handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '请先登录' }
      return { items: USER_STATE.subscriptions[user.id] || [] }
    },
  },
  {
    method: 'DELETE', path: '/api/subscriptions/:id', handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '请先登录' }
      USER_STATE.subscriptions[user.id] = (USER_STATE.subscriptions[user.id] || []).filter((item) => item.id !== Number(req.params.id))
      return { success: true }
    },
  },
  {
    method: 'GET', path: '/api/notifications', handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '请先登录' }
      const read = new URL(req.url, 'http://localhost:5000').searchParams.get('is_read')
      const items = USER_STATE.notifications[user.id] || []
      return { items: read === null ? items : items.filter((item) => String(item.read) === read) }
    },
  },
  {
    method: 'PUT', path: '/api/notifications/:id/read', handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '请先登录' }
      const item = (USER_STATE.notifications[user.id] || []).find((candidate) => candidate.id === Number(req.params.id))
      if (!item) return { __status: 404, message: '通知不存在' }
      item.read = true
      return { success: true }
    },
  },
]
