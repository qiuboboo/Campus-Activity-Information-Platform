/**
 * 日历相关 Mock 路由
 *   GET /api/calendar/events
 */

import { CALENDAR_EVENTS } from '../db.js'
import { getToken } from '../utils.js'

export default [
  {
    method: 'GET',
    path: '/api/calendar/events',
    handler: async (req) => {
      const token = getToken(req)
      if (!token) return { events: [] }

      // 从 token 中提取用户 id（mock 简化：admin=1, zhangsan=2, 注册用户≥3）
      const userId = token.includes('admin') ? 1 : 2
      return { events: CALENDAR_EVENTS[userId] || [] }
    },
  },
]
