/**
 * 前端 Mock API 服务器
 * 纯前端开发时使用，无需启动后端。
 * 监听 5000 端口，模拟所有后端 `/api/*` 接口。
 *
 * 启动方式：node mock-server.js
 * （然后在另一个终端运行 npm run dev）
 */

import http from 'node:http'

const PORT = 5000

// ==================== 模拟数据 ====================

const DEMO_USER = {
  id: 1,
  username: 'admin',
  role: 'admin',
  created_at: '2026-01-01T00:00:00',
}

const POSTERS = [
  {
    id: 1,
    title: '2026 校园科技文化节开幕式',
    raw_text: '2026 校园科技文化节将于 2026-05-10 19:00 在大学生活动中心大礼堂举行，由校团委主办。',
    summary: '校园科技文化节开幕式，面向全校师生开放。',
    event_time: '2026-05-10T19:00:00',
    location: '大学生活动中心大礼堂',
    organizer: '校团委',
    status: 'published',
    source_type: 'manual',
    source_url: 'https://example.edu.cn/events/tech-culture-opening',
    created_by: 1,
    created_at: '2026-04-01T10:00:00',
  },
  {
    id: 2,
    title: 'AI 创新应用讲座',
    raw_text: 'AI 创新应用讲座将于 2026-05-10 15:00 在大学生活动中心大礼堂举行，由计算机学院主办。',
    summary: '面向全校学生的人工智能应用讲座。',
    event_time: '2026-05-10T15:00:00',
    location: '大学生活动中心大礼堂',
    organizer: '计算机学院',
    status: 'published',
    source_type: 'manual',
    source_url: 'https://example.edu.cn/events/ai-lecture',
    created_by: 1,
    created_at: '2026-04-02T10:00:00',
  },
  {
    id: 3,
    title: '校园志愿服务文化论坛',
    raw_text: '校园志愿服务文化论坛将于 2026-05-12 14:00 在图书馆报告厅举行，由校团委主办。',
    summary: '围绕校园志愿服务与文化建设开展交流。',
    event_time: '2026-05-12T14:00:00',
    location: '图书馆报告厅',
    organizer: '校团委',
    status: 'published',
    source_type: 'manual',
    source_url: 'https://example.edu.cn/events/volunteer-forum',
    created_by: 1,
    created_at: '2026-04-03T10:00:00',
  },
  {
    id: 4,
    title: '春季篮球联赛决赛',
    raw_text: '春季篮球联赛决赛将于 2026-05-15 16:00 在校体育馆举行，由体育部主办。',
    summary: '各学院代表队角逐冠军。',
    event_time: '2026-05-15T16:00:00',
    location: '校体育馆',
    organizer: '体育部',
    status: 'published',
    source_type: 'manual',
    source_url: 'https://example.edu.cn/events/basketball-final',
    created_by: 1,
    created_at: '2026-04-05T10:00:00',
  },
  {
    id: 5,
    title: '校园歌手大赛海选',
    raw_text: '校园歌手大赛海选将于 2026-05-18 18:00 在音乐厅举行，由校学生会主办。',
    summary: '面向全校学生的歌唱比赛海选。',
    event_time: '2026-05-18T18:00:00',
    location: '音乐厅',
    organizer: '校学生会',
    status: 'pending_review',
    source_type: 'manual',
    source_url: '',
    created_by: 1,
    created_at: '2026-04-10T10:00:00',
  },
  {
    id: 6,
    title: '考研经验分享会',
    raw_text: '考研经验分享会将于 2026-05-20 14:00 在教学楼 101 教室举行，由学习部主办。',
    summary: '邀请优秀学长学姐分享考研备考经验。',
    event_time: '2026-05-20T14:00:00',
    location: '教学楼 101 教室',
    organizer: '学习部',
    status: 'draft',
    source_type: 'manual',
    source_url: '',
    created_by: 1,
    created_at: '2026-04-15T10:00:00',
  },
]

const KNOWLEDGE_NODES = [
  { id: 1, poster_id: 1, label: '校园科技文化节', category: '活动', properties: '{"date":"2026-05-10","location":"大礼堂"}' },
  { id: 2, poster_id: 1, label: '校团委', category: '组织', properties: '{}' },
  { id: 3, poster_id: 2, label: 'AI 创新应用讲座', category: '活动', properties: '{"date":"2026-05-10","location":"大礼堂"}' },
  { id: 4, poster_id: 2, label: '计算机学院', category: '组织', properties: '{}' },
  { id: 5, poster_id: 1, label: '大学生活动中心', category: '地点', properties: '{}' },
]

const KNOWLEDGE_LINKS = [
  { id: 1, source_node_id: 1, target_node_id: 2, relation: '主办单位' },
  { id: 2, source_node_id: 3, target_node_id: 4, relation: '主办单位' },
  { id: 3, source_node_id: 1, target_node_id: 5, relation: '举办地点' },
]

const SOURCES = [
  { id: 1, name: '学校官网', type: 'website', base_url: 'https://www.example.edu.cn', is_active: true, last_crawled_at: null },
  { id: 2, name: '团委公众号', type: 'wechat', base_url: 'https://mp.weixin.qq.com', is_active: true, last_crawled_at: null },
]

const AUDIT_LOGS = [
  { id: 1, poster_id: 5, action: 'submit', reviewer_id: null, comment: null, created_at: '2026-04-10T10:00:00' },
]

// ==================== 工具函数 ====================

let currentPosterId = 7
let currentNodeId = 6
let currentLinkId = 4

function jsonResponse(res, data, status = 200) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
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
  const auth = req.headers['authorization'] || ''
  return auth.startsWith('Bearer ') ? auth.slice(7) : null
}

// ==================== 路由 ====================

const routes = {
  // --- 健康检查 ---
  'GET /api/health': async (_req) => ({
    status: 'ok',
    database: 'ok',
    service: 'campus-activity-backend (mock)',
    timestamp: new Date().toISOString(),
  }),

  // --- 认证 ---
  'POST /api/auth/login': async (req) => {
    const { username, password } = await parseBody(req)
    if (username === 'admin' && password === 'admin123456') {
      return {
        token: 'mock-jwt-token-' + Date.now(),
        user: DEMO_USER,
      }
    }
    return { message: 'invalid credentials' }
  },
  'POST /api/auth/login 401': async (req) => {
    return { message: 'invalid credentials' }
  },

  'GET /api/auth/me': async (req) => {
    const token = getToken(req)
    if (!token) return { user: null }
    return { user: DEMO_USER }
  },

  // --- 海报 ---
  'GET /api/posters': async (req) => {
    const url = new URL(req.url, `http://localhost:${PORT}`)
    const page = parseInt(url.searchParams.get('page') || '1')
    const perPage = parseInt(url.searchParams.get('per_page') || '10')
    const status = url.searchParams.get('status')
    const keyword = url.searchParams.get('keyword')
    let list = [...POSTERS]
    if (status) list = list.filter((p) => p.status === status)
    if (keyword) list = list.filter((p) => p.title.includes(keyword) || p.summary?.includes(keyword))
    const total = list.length
    const start = (page - 1) * perPage
    const items = list.slice(start, start + perPage)
    return { items, total, page, per_page: perPage, pages: Math.ceil(total / perPage) }
  },

  // --- 首页精选 ---
  'GET /api/home/featured': async () => {
    const featured = POSTERS.filter((p) => p.status === 'published').slice(0, 3)
    return { items: featured }
  },

  'GET /api/posters/:id': async (req, id) => {
    const poster = POSTERS.find((p) => p.id === Number(id))
    if (!poster) return { message: 'not found' }
    return { poster }
  },

  'POST /api/posters': async (req) => {
    const body = await parseBody(req)
    const poster = {
      id: currentPosterId++,
      ...body,
      created_by: 1,
      created_at: new Date().toISOString(),
      status: body.status || 'draft',
    }
    POSTERS.push(poster)
    return { poster }
  },

  'PUT /api/posters/:id': async (req, id) => {
    const body = await parseBody(req)
    const idx = POSTERS.findIndex((p) => p.id === Number(id))
    if (idx === -1) return { message: 'not found' }
    POSTERS[idx] = { ...POSTERS[idx], ...body }
    return { poster: POSTERS[idx] }
  },

  'POST /api/posters/:id/review': async (req, id) => {
    const body = await parseBody(req)
    const idx = POSTERS.findIndex((p) => p.id === Number(id))
    if (idx === -1) return { message: 'not found' }
    POSTERS[idx].status = body.status || 'published'
    AUDIT_LOGS.push({
      id: AUDIT_LOGS.length + 1,
      poster_id: Number(id),
      action: body.status === 'approved' ? 'approve' : 'reject',
      reviewer_id: 1,
      comment: body.comment || '',
      created_at: new Date().toISOString(),
    })
    return { poster: POSTERS[idx] }
  },

  'POST /api/posters/:id/submit': async (_req, id) => {
    const idx = POSTERS.findIndex((p) => p.id === Number(id))
    if (idx === -1) return { message: 'not found' }
    POSTERS[idx].status = 'pending_review'
    return { poster: POSTERS[idx] }
  },

  // --- 知识图谱 ---
  'GET /api/knowledge/nodes': async () => ({
    nodes: KNOWLEDGE_NODES,
    links: KNOWLEDGE_LINKS,
  }),

  'GET /api/knowledge/nodes/:id': async (_req, id) => {
    const node = KNOWLEDGE_NODES.find((n) => n.id === Number(id))
    if (!node) return { message: 'not found' }
    const relatedLinks = KNOWLEDGE_LINKS.filter(
      (l) => l.source_node_id === node.id || l.target_node_id === node.id,
    )
    const relatedNodeIds = new Set(
      relatedLinks.flatMap((l) => [l.source_node_id, l.target_node_id]),
    )
    const relatedNodes = KNOWLEDGE_NODES.filter((n) => relatedNodeIds.has(n.id) && n.id !== node.id)
    return { node, links: relatedLinks, related_nodes: relatedNodes }
  },

  // --- 搜索 ---
  'GET /api/search': async (req) => {
    const url = new URL(req.url, `http://localhost:${PORT}`)
    const q = url.searchParams.get('q') || ''
    const results = POSTERS.filter(
      (p) => p.title.includes(q) || p.summary?.includes(q) || p.raw_text?.includes(q),
    )
    return { results, total: results.length, query: q }
  },

  'GET /api/search/external': async (req) => {
    const url = new URL(req.url, `http://localhost:${PORT}`)
    const q = url.searchParams.get('q') || ''
    return {
      results: [
        { title: `外部结果：${q}`, url: 'https://example.com', snippet: `关于"${q}"的外部搜索结果示例。` },
        { title: `"${q}" 相关信息`, url: 'https://example.org', snippet: `更多与"${q}"相关的外部信息。` },
      ],
      total: 2,
      query: q,
    }
  },

  // --- 数据源 ---
  'GET /api/data-sources': async () => ({ items: SOURCES }),
  'POST /api/data-sources': async (req) => {
    const body = await parseBody(req)
    const ds = { id: SOURCES.length + 1, ...body, is_active: true, last_crawled_at: null }
    SOURCES.push(ds)
    return { data_source: ds }
  },
  'DELETE /api/data-sources/:id': async (_req, id) => {
    const idx = SOURCES.findIndex((s) => s.id === Number(id))
    if (idx !== -1) SOURCES.splice(idx, 1)
    return { message: 'deleted' }
  },
  'POST /api/data-sources/:id/crawl': async () => ({
    message: 'crawl task started',
    task_id: 'mock-task-' + Date.now(),
  }),

  // --- 字典 ---
  'GET /api/dicts/:type': async (_req, type) => ({
    items: [
      { code: type === 'poster_status' ? 'published' : 'lecture', label: type === 'poster_status' ? '已发布' : '讲座' },
      { code: type === 'poster_status' ? 'draft' : 'competition', label: type === 'poster_status' ? '草稿' : '竞赛' },
      { code: type === 'poster_status' ? 'pending_review' : 'volunteer', label: type === 'poster_status' ? '待审核' : '志愿' },
    ],
  }),

  // --- 审计日志 ---
  'GET /api/audit-logs': async () => ({ items: AUDIT_LOGS }),

  // --- AI ---
  'POST /api/ai/analyze': async (req) => {
    const body = await parseBody(req)
    return {
      result: `已分析内容：${(body.text || '').slice(0, 50)}...`,
      suggestions: ['建议添加活动详情', '建议补充联系信息'],
      summary: 'AI 分析完成（Mock）',
    }
  },

  // --- 仪表盘摘要 ---
  'GET /api/demo/summary': async () => {
    const published = POSTERS.filter((p) => p.status === 'published').length
    const draft = POSTERS.filter((p) => p.status === 'draft' || p.status === 'pending_review').length
    return {
      posters: {
        total: POSTERS.length,
        published,
        draft,
        rejected: 0,
      },
      knowledge_nodes: KNOWLEDGE_NODES.length,
      poster_links: KNOWLEDGE_LINKS.length,
      data_sources: SOURCES.length,
      last_crawl: SOURCES.some((s) => s.last_crawled_at)
        ? {
            id: 1,
            data_source_id: 1,
            status: 'completed',
            pages_found: 5,
            pages_succeeded: 4,
            drafts_created: 2,
            average_quality_score: 8.5,
            started_at: new Date(Date.now() - 3600000).toISOString(),
            finished_at: new Date().toISOString(),
          }
        : null,
    }
  },

  // --- 导出 ---
  'GET /api/export/:format': async (_req, format) => ({
    message: `导出格式 ${format} 已生成（Mock）`,
    url: `/mock-exports/activities.${format}`,
  }),

  // --- 任务 ---
  'POST /api/tasks': async () => ({ task_id: 'mock-task-' + Date.now(), status: 'pending' }),
  'GET /api/tasks/:id': async () => ({ status: 'completed', result: 'mock result' }),
}

// ==================== 服务器 ====================

const server = http.createServer(async (req, res) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    })
    return res.end()
  }

  const url = req.url || '/'
  const method = req.method || 'GET'

  // 尝试精确匹配
  const exactKey = `${method} ${url.split('?')[0]}`
  if (routes[exactKey]) {
    try { return jsonResponse(res, await routes[exactKey](req)) }
    catch (e) { return jsonResponse(res, { error: e.message }, 500) }
  }

  // 尝试参数化匹配（含路径参数）
  for (const [key, handler] of Object.entries(routes)) {
    const [routeMethod, routePath] = key.split(' ')
    if (routeMethod !== method) continue

    const routeParts = routePath.split('/')
    const pathname = url.split('?')[0]
    const urlParts = pathname.split('/')

    if (routeParts.length !== urlParts.length) continue

    const params = {}
    let match = true
    for (let i = 0; i < routeParts.length; i++) {
      if (routeParts[i].startsWith(':')) {
        params[routeParts[i].slice(1)] = urlParts[i]
      } else if (routeParts[i] !== urlParts[i]) {
        match = false
        break
      }
    }

    if (match) {
      // 处理 401 后缀特殊路由
      const handlerKey = key.includes(' 401')
        ? key
        : `${method} ${routePath} 401`
      if (handlerKey && routes[handlerKey]) {
        // 带 token 校验的路由
        if (!getToken(req)) {
          return jsonResponse(res, await routes[handlerKey](req), 401)
        }
      }

      try {
        const data = await handler(req, params)
        const status = key.endsWith(' 401') ? 401 : 200
        return jsonResponse(res, data, status)
      } catch (e) {
        return jsonResponse(res, { error: e.message }, 500)
      }
    }
  }

  // 404
  jsonResponse(res, { message: `Mock: ${method} ${url} not implemented` }, 404)
})

server.listen(PORT, () => {
  console.log(`\n  🎭 Mock API 服务器运行在 http://localhost:${PORT}`)
  console.log(`  📋 支持的接口列表：`)
  console.log(`     GET  /api/health`)
  console.log(`     POST /api/auth/login (admin / admin123456)`)
  console.log(`     GET  /api/auth/me`)
  console.log(`     GET  /api/posters`)
  console.log(`     GET  /api/posters/:id`)
  console.log(`     POST /api/posters`)
  console.log(`     PUT  /api/posters/:id`)
  console.log(`     POST /api/posters/:id/review`)
  console.log(`     POST /api/posters/:id/submit`)
  console.log(`     GET  /api/knowledge/nodes`)
  console.log(`     GET  /api/knowledge/nodes/:id`)
  console.log(`     GET  /api/search`)
  console.log(`     GET  /api/search/external`)
  console.log(`     GET  /api/data-sources`)
  console.log(`     POST /api/data-sources`)
  console.log(`     GET  /api/dicts/:type`)
  console.log(`     GET  /api/audit-logs`)
  console.log(`     POST /api/ai/analyze`)
  console.log(`     GET  /api/export/:format`)
  console.log(`     POST /api/tasks`)
  console.log(`     GET  /api/tasks/:id`)
  console.log(`\n  🔗 Vite 开发服务器: http://localhost:3000`)
  console.log(`  📌 请在另一个终端运行: npm run dev\n`)
})
