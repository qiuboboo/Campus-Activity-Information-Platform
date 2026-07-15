/**
 * Activity Mock routes. These mirror the frontend contract, including ownership
 * and publication boundaries, without replacing the real backend's authorization.
 */
import { ACTIVITIES, CALENDAR_EVENTS, UPLOADS, USER_STATE, getNextActivityId } from '../db.js'
import { getCurrentUser, parseBody } from '../utils.js'

const PORT = 5000

function page(items, url) {
  const current = Math.max(Number(url.searchParams.get('page') || 1), 1)
  const perPage = Math.max(Number(url.searchParams.get('per_page') || 10), 1)
  return { items: items.slice((current - 1) * perPage, current * perPage), total: items.length, page: current, per_page: perPage, pages: Math.ceil(items.length / perPage) }
}

function sortActivities(items, sort) {
  const sorted = [...items]
  if (sort === 'event_time') {
    sorted.sort((a, b) => (new Date(a.event_time || '9999-12-31').getTime() - new Date(b.event_time || '9999-12-31').getTime()) || a.id - b.id)
  } else if (sort === 'created_at' || sort === 'relevance') {
    sorted.sort((a, b) => (new Date(b.created_at).getTime() - new Date(a.created_at).getTime()) || a.id - b.id)
  }
  return sorted
}

function canManageActivity(user, activity) {
  return user?.role === 'admin' || activity.created_by === user?.id
}

function visibleDetail(activity, user) {
  return activity.status === 'published' || canManageActivity(user, activity)
}

function resolveAttachments(user, attachments) {
  if (!Array.isArray(attachments)) return { error: '附件格式无效' }
  const resolved = []
  for (const attachment of attachments) {
    const upload = UPLOADS.get(String(attachment?.id || ''))
    if (!upload || (user.role !== 'admin' && upload.owner_id !== user.id)) return { error: '附件不存在或无权使用' }
    resolved.push({ id: upload.id, name: upload.name, url: upload.url, mime_type: upload.mime_type, size: upload.size })
  }
  return { attachments: resolved }
}

export default [
  {
    method: 'GET', path: '/api/activities/mine', handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '请先登录' }
      const url = new URL(req.url, `http://localhost:${PORT}`)
      const status = url.searchParams.get('status')
      const keyword = url.searchParams.get('q') || ''
      let items = ACTIVITIES.filter((item) => user.role === 'admin' || item.created_by === user.id)
      if (status) items = items.filter((item) => item.status === status)
      if (keyword) items = items.filter((item) => item.title.includes(keyword))
      return page(items, url)
    },
  },
  {
    method: 'GET', path: '/api/activities', handler: async (req) => {
      const url = new URL(req.url, `http://localhost:${PORT}`)
      const user = getCurrentUser(req)
      const status = url.searchParams.get('status')
      const keyword = url.searchParams.get('keyword') || url.searchParams.get('q') || ''
      const activityType = url.searchParams.get('activity_type')
      const sort = url.searchParams.get('sort')
      let items = [...ACTIVITIES]
      if (status && status !== 'published') {
        if (!user) return { __status: 403, message: '权限不足' }
        items = items.filter((item) => item.status === status && canManageActivity(user, item))
      } else {
        items = items.filter((item) => item.status === 'published')
      }
      if (activityType) items = items.filter((item) => item.activity_type === activityType)
      if (keyword) items = items.filter((item) => [item.title, item.summary, item.raw_text, item.location, item.organizer].some((value) => value?.includes(keyword)))
      return page(sortActivities(items, sort), url)
    },
  },
  {
    method: 'POST', path: '/api/activities', handler: async (req) => {
      const user = getCurrentUser(req)
      if (!user) return { __status: 401, message: '请先登录' }
      if (!['publisher', 'admin'].includes(user.role)) return { __status: 403, message: '权限不足' }
      const body = await parseBody(req)
      if (!body.title || !body.raw_text) return { __status: 422, message: '标题和正文不能为空' }
      const attachmentResult = resolveAttachments(user, body.attachments || [])
      if (attachmentResult.error) return { __status: 422, message: attachmentResult.error }
      const activity = { id: getNextActivityId(), ...body, attachments: attachmentResult.attachments, status: 'draft', created_by: user.id, created_at: new Date().toISOString(), meta: { views: 0, registrations: 0 } }
      ACTIVITIES.push(activity)
      return activity
    },
  },
  {
    method: 'PUT', path: '/api/activities/:id', handler: async (req) => {
      const user = getCurrentUser(req)
      const activity = ACTIVITIES.find((item) => item.id === Number(req.params.id))
      if (!user) return { __status: 401, message: '请先登录' }
      if (!activity) return { __status: 404, message: 'activity not found' }
      if (!canManageActivity(user, activity)) return { __status: 403, message: '权限不足' }
      if (!['draft', 'rejected'].includes(activity.status)) return { __status: 409, message: '当前状态不可编辑' }
      const body = await parseBody(req)
      const attachmentResult = resolveAttachments(user, body.attachments || [])
      if (attachmentResult.error) return { __status: 422, message: attachmentResult.error }
      Object.assign(activity, body, { attachments: attachmentResult.attachments })
      return activity
    },
  },
  {
    method: 'POST', path: '/api/activities/:id/submit-review', handler: async (req) => {
      const user = getCurrentUser(req)
      const activity = ACTIVITIES.find((item) => item.id === Number(req.params.id))
      if (!user) return { __status: 401, message: '请先登录' }
      if (!activity) return { __status: 404, message: 'activity not found' }
      if (!canManageActivity(user, activity)) return { __status: 403, message: '权限不足' }
      if (!['draft', 'rejected'].includes(activity.status)) return { __status: 409, message: '当前状态不可提交审核' }
      activity.status = 'pending_review'
      return activity
    },
  },
  {
    method: 'GET', path: '/api/activities/:id', handler: async (req) => {
      const activity = ACTIVITIES.find((item) => item.id === Number(req.params.id))
      const user = getCurrentUser(req)
      if (!activity || !visibleDetail(activity, user)) return { __status: 404, message: 'activity not found' }
      return {
        ...activity,
        tags: activity.tags || ['学术', '公开'],
        attachments: activity.attachments || [{ url: '/media/activity-cover.png', name: '活动海报' }],
        meta: activity.meta || { views: 128, registrations: 36 },
        favorite: Boolean(user && (USER_STATE.favorites[user.id] || []).includes(activity.id)),
        registered: Boolean(user && (USER_STATE.registrations[activity.id] || []).includes(user.id)),
        in_calendar: Boolean(user && (CALENDAR_EVENTS[user.id] || []).some((event) => event.activity_id === activity.id)),
        source_name: activity.source_name || activity.organizer || '校园公开信息源',
        source_url: activity.source_url || 'https://www.sysu.edu.cn',
      }
    },
  },
  { method: 'POST', path: '/api/activities/:id/favorite', handler: async (req) => { const user = getCurrentUser(req); if (!user) return { __status: 401, message: '请先登录' }; const ids = USER_STATE.favorites[user.id] ||= []; const id = Number(req.params.id); if (!ids.includes(id)) ids.push(id); return { favorite: true } } },
  { method: 'DELETE', path: '/api/activities/:id/favorite', handler: async (req) => { const user = getCurrentUser(req); if (!user) return { __status: 401, message: '请先登录' }; USER_STATE.favorites[user.id] = (USER_STATE.favorites[user.id] || []).filter((id) => id !== Number(req.params.id)); return { favorite: false } } },
  {
    method: 'POST', path: '/api/activities/:id/register', handler: async (req) => {
      const user = getCurrentUser(req)
      const activity = ACTIVITIES.find((item) => item.id === Number(req.params.id))
      if (!user) return { __status: 401, message: '请先登录' }
      if (!activity || activity.status !== 'published') return { __status: 404, message: 'activity not found' }
      const registeredUsers = USER_STATE.registrations[activity.id] ||= []
      activity.meta = activity.meta || { views: 0, registrations: 0 }
      if (registeredUsers.includes(user.id)) return { success: true, already_registered: true, registrations: activity.meta.registrations || 0 }
      registeredUsers.push(user.id)
      activity.meta.registrations = (activity.meta.registrations || 0) + 1
      return { success: true, already_registered: false, registrations: activity.meta.registrations }
    },
  },
  {
    method: 'GET', path: '/api/search/internal', handler: async (req) => {
      const url = new URL(req.url, `http://localhost:${PORT}`)
      const q = url.searchParams.get('q') || ''
      const type = url.searchParams.get('activity_type')
      const sort = url.searchParams.get('sort')
      const matches = sortActivities(ACTIVITIES.filter((item) => item.status === 'published' && (item.title.includes(q) || item.summary.includes(q)) && (!type || item.activity_type === type)), sort)
      const result = page(matches, url)
      return { ...result, search_mode: 'vector', items: result.items.map((item) => ({ hit_type: 'activity', item, score: 0.8 })) }
    },
  },
  {
    method: 'GET', path: '/api/search/external', handler: async (req) => {
      const url = new URL(req.url, `http://localhost:${PORT}`)
      const q = url.searchParams.get('q') || ''
      const type = url.searchParams.get('activity_type')
      const sort = url.searchParams.get('sort')
      const matches = sortActivities(ACTIVITIES.filter((item) => item.status === 'published' && (item.title.includes(q) || item.summary.includes(q)) && (!type || item.activity_type === type)), sort)
      const result = page(matches, url)
      return { ...result, search_mode: 'fulltext', items: result.items.map((item) => ({ hit_type: 'external', item, score: 0.6, source: 'Mock external search' })) }
    },
  },
  {
    method: 'GET', path: '/api/export/posters.json', handler: async (req) => {
      const user = getCurrentUser(req)
      if (user?.role !== 'admin') return { __status: user ? 403 : 401, message: user ? '权限不足' : '请先登录' }
      return { items: ACTIVITIES, total: ACTIVITIES.length }
    },
  },
]
