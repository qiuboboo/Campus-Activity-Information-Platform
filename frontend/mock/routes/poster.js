/**
 * 活动相关 Mock 路由
 *   GET /api/posters
 */

import { POSTERS } from '../db.js'

const PORT = 5000

export default [
  {
    method: 'GET',
    path: '/api/posters',
    handler: async (req) => {
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
  },
]
