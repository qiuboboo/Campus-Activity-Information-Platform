/**
 * 活动相关 Mock 路由
 *   GET /api/activities
 *   GET /api/activities/:id
 */

import { ACTIVITIES } from '../db.js'

const PORT = 5000

export default [
  {
    method: 'GET',
    path: '/api/activities',
    handler: async (req) => {
      const url = new URL(req.url, `http://localhost:${PORT}`)
      const page = Math.max(parseInt(url.searchParams.get('page') || '1', 10), 1)
      const perPage = Math.max(parseInt(url.searchParams.get('per_page') || '10', 10), 1)
      const status = url.searchParams.get('status')
      const keyword = url.searchParams.get('keyword') || url.searchParams.get('q')

      let items = [...ACTIVITIES]
      if (status) items = items.filter((a) => a.status === status)
      if (keyword) {
        items = items.filter((a) =>
          a.title.includes(keyword)
          || a.summary.includes(keyword)
          || a.raw_text.includes(keyword)
          || a.location.includes(keyword)
          || a.organizer.includes(keyword),
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
  },
  {
    method: 'GET',
    path: '/api/activities/:id',
    handler: async (req) => {
      const id = Number(req.params?.id)
      const activity = ACTIVITIES.find((item) => item.id === id)

      if (!activity) {
        return { __status: 404, message: 'activity not found' }
      }

      return {
        ...activity,
        tags: activity.tags || ['学术', '公开'],
        attachments: activity.attachments || [{ url: '/media/activity-cover.png', name: '活动海报' }],
        meta: activity.meta || { views: 128, registrations: 36 },
      }
    },
  },
  {
    method: 'POST',
    path: '/api/activities/:id/register',
    handler: async (req) => {
      const id = Number(req.params?.id)
      const activity = ACTIVITIES.find((item) => item.id === id)
      if (!activity) return { __status: 404, message: 'activity not found' }
      // 简单模拟报名成功并增加 registrations 计数（内存）
      activity.meta = activity.meta || { views: 0, registrations: 0 }
      activity.meta.registrations = (activity.meta.registrations || 0) + 1
      return { success: true, registrations: activity.meta.registrations }
    },
  },
  {
    method: 'GET',
    path: '/api/search/internal',
    handler: async (req) => {
      const url = new URL(req.url, `http://localhost:${PORT}`)
      const q = url.searchParams.get('q') || ''
      const items = ACTIVITIES.filter((a) => a.title.includes(q) || a.summary.includes(q)).slice(0, 10)
      return {
        search_mode: 'vector',
        items: items.map((item) => ({ hit_type: 'activity', item, score: 0.8 })),
        total: items.length,
      }
    },
  },
  {
    method: 'GET',
    path: '/api/search/external',
    handler: async (req) => {
      const url = new URL(req.url, `http://localhost:${PORT}`)
      const q = url.searchParams.get('q') || ''
      const items = ACTIVITIES.filter((a) => a.title.includes(q) || a.summary.includes(q)).slice(0, 5)
      return {
        search_mode: 'fulltext',
        items: items.map((item) => ({ hit_type: 'activity', item, score: 0.6 })),
        total: items.length,
      }
    },
  },
  {
    method: 'GET',
    path: '/api/export/activities.json',
    handler: async () => ({ items: ACTIVITIES, total: ACTIVITIES.length }),
  },
]
