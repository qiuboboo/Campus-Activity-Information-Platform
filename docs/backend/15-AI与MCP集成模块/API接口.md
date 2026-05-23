# AI 与 MCP 集成模块 API

---

## AI 服务

### `GET /api/ai/status`

查看 AI 服务状态（LLM 和 MCP 配置情况）。

**权限：** 需 JWT 认证（任意角色）

**查询参数：** 无

**成功响应 (200)：**
```json
{
  "llm_configured": true,
  "mcp_servers": {
    "xiaohongshu": { "command": "npx", "running": true },
    "search": { "command": "npx", "running": false }
  }
}
```

**错误码：**
- `401`：未提供或无效的 JWT

---

### `POST /api/ai/extract`

调用 LLM 对活动文本进行结构化字段提取。当 LLM 不可用时自动降级到基于正则表达式的兜底提取。

**权限：** 需 JWT 认证（任意角色）

**请求体：**
```json
{
  "text": "校园科技文化节开幕式将于2026年5月10日晚7点在大礼堂举行，由校团委主办",
  "model": "default"
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | 是 | 活动文本内容，最长截取前 4000 字符 |
| `model` | string | 否 | 指定 LLM profile 名称（如 `"copilot"`、`"deepseek"`），不传则使用默认配置 |

**成功响应 (200)：**
```json
{
  "fields": {
    "title": "校园科技文化节开幕式",
    "event_time": "2026-05-10T19:00:00",
    "location": "大礼堂",
    "organizer": "校团委",
    "summary": "校园科技文化节开幕式将于2026年5月10日晚7点在大礼堂举行...",
    "tags": ["科技", "校园文化"],
    "activity_type": "其他"
  }
}
```

当使用兜底提取时（LLM 不可用），额外返回 `_fallback: true` 标记：
```json
{
  "fields": {
    "title": "校园科技文化节开幕式",
    "event_time": "2026-05-10T19:00:00",
    "_fallback": true
  }
}
```

**错误码：**
- `400`：`text` 为空 — `{"error": "text is required"}`
- `503`：LLM 不可用且兜底提取也失败 — `{"error": "Extraction failed (LLM unavailable)", "fields": {}}`
- `401`：未提供或无效的 JWT

---

### `POST /api/ai/enrich/{poster_id}`

对指定海报调用 LLM 生成摘要、分类标签、完善字段。仅管理员可调用。

**权限：** `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `poster_id` | int | 海报 ID |

**请求体：** 无

**成功响应 (200)：**
```json
{
  "item": {
    "id": 42,
    "title": "校园科技文化节",
    "summary": "一年一度的校园科技文化节...",
    "tags": "科技,校园文化,创新",
    "activity_type": "其他",
    "status": "published",
    ...
  },
  "ai_result": {
    "summary": "一年一度的校园科技文化节，包含科技创新展览、编程竞赛和学术论坛等活动",
    "tags": ["科技", "校园文化", "创新", "竞赛"],
    "activity_type": "其他",
    "keywords": ["科技节", "创新", "竞赛", "展览"],
    "related_suggestions": ["科技创新大赛", "学术论坛"]
  }
}
```

**错误码：**
- `503`：LLM 不可用或海报不存在 — `{"error": "Enrichment failed (LLM unavailable or poster not found)"}`
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

### `POST /api/ai/search`

AI 驱动的高级搜索，支持多引擎搜索和 LLM 兜底。

**权限：** 需 JWT 认证（任意角色）

**请求体：**
```json
{
  "query": "中山大学 2025 科技节",
  "sources": ["web", "sogou", "llm"]
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 搜索查询 |
| `sources` | string[] | 否 | 搜索源列表。可选值：`"web"`（SearXNG 多引擎搜索: google, bing, duckduckgo, baidu）、`"sogou"`（搜狗微信搜索）、`"llm"`（LLM 兜底搜索，搜索引擎无结果时使用）。不传则默认使用所有真实搜索引擎（不含 LLM 兜底） |

**成功响应 (200)：**
```json
{
  "query": "中山大学 2025 科技节",
  "results": [
    {
      "title": "中山大学2025年科技文化节",
      "summary": "中山大学将于2025年5月举办科技文化节系列活动...",
      "source": "search_web",
      "url": "https://www.sysu.edu.cn/..."
    }
  ],
  "count": 5
}
```

**错误码：**
- `400`：`query` 为空 — `{"error": "query is required"}`
- `401`：未认证

---

## MCP 服务管理

### `GET /api/ai/mcp/servers`

查看已配置的 MCP 服务器列表及运行状态。

**权限：** 需 JWT 认证（任意角色）

**查询参数：** 无

**成功响应 (200)：**
```json
{
  "servers": {
    "xiaohongshu": { "command": "npx", "running": true },
    "search": { "command": "npx", "running": false }
  }
}
```

**错误码：**
- `401`：未认证

---

### `POST /api/ai/mcp/call`

调用指定 MCP 服务器的工具。仅管理员可调用。

**权限：** `admin`

**请求体：**
```json
{
  "server": "xiaohongshu",
  "tool": "search_notes",
  "params": { "query": "校园活动", "limit": 10 }
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `server` | string | 是 | MCP 服务器名称，需在环境变量 `MCP_SERVERS` 中配置 |
| `tool` | string | 是 | 要调用的工具名称 |
| `params` | object | 否 | 工具参数对象 |

**成功响应 (200)：**
```json
{
  "server": "xiaohongshu",
  "tool": "search_notes",
  "result": [
    {
      "id": "note_id_123",
      "title": "校园科技节来啦！",
      "likes": 1200
    }
  ]
}
```

**错误码：**
- `400`：`server` 或 `tool` 为空 — `{"error": "server is required"}`
- `503`：MCP 服务器未配置或不可用 — `{"error": "MCP call failed (server 'xxx' unavailable or not configured)"}`
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

## 受控词表（Dict）

### `GET /api/dict/{category}`

获取指定类别的词条列表，支持搜索和分页。

**权限：** 需 JWT 认证（任意角色）

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `category` | string | 词表类别，取值 `place`（地点）、`org`（组织）、`topic`（主题） |

**查询参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 否 | — | 搜索关键词，匹配标准名称和别名 |
| `page` | int | 否 | `1` | 页码 |
| `per_page` | int | 否 | `50` | 每页条数，最大 `200` |

**成功响应 (200)：**
```json
{
  "category": "place",
  "items": [
    {
      "id": 1,
      "category": "place",
      "standard_name": "大学生活动中心",
      "aliases": "大活,活动中心",
      "description": "校内主要学生活动场所",
      "created_at": "2026-01-01T00:00:00",
      "updated_at": "2026-01-01T00:00:00"
    }
  ],
  "page": 1,
  "per_page": 50,
  "total": 1
}
```

**错误码：**
- `401`：未认证

---

### `POST /api/dict/{category}`

新增词条。仅管理员可调用。

**权限：** `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `category` | string | 词表类别，取值 `place`、`org`、`topic` |

**请求体：**
```json
{
  "standard_name": "大学生活动中心",
  "aliases": "大活,活动中心",
  "description": "校内主要学生活动场所"
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `standard_name` | string | 是 | 标准名称 |
| `aliases` | string | 否 | 别名，多个别名用逗号分隔 |
| `description` | string | 否 | 说明 |

**成功响应 (201)：**
```json
{
  "item": {
    "id": 1,
    "category": "place",
    "standard_name": "大学生活动中心",
    "aliases": "大活,活动中心",
    "description": "校内主要学生活动场所",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00"
  }
}
```

**错误码：**
- `400`：`standard_name` 为空或类别无效 — `{"error": "standard_name is required"}`
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

### `PUT /api/dict/{category}/{id}`

编辑词条。仅管理员可调用。

**权限：** `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `category` | string | 词表类别 |
| `id` | int | 词条 ID |

**请求体：**
```json
{
  "standard_name": "新标准名称",
  "aliases": "新别名1,新别名2",
  "description": "新的说明"
}
```

**成功响应 (200)：**
```json
{
  "item": {
    "id": 1,
    "category": "place",
    "standard_name": "新标准名称",
    "aliases": "新别名1,新别名2",
    "description": "新的说明",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-05-24T00:00:00"
  }
}
```

**错误码：**
- `404`：词条不存在 — `{"error": "Entry not found"}`
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

### `DELETE /api/dict/{category}/{id}`

删除词条。仅管理员可调用。

**权限：** `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `category` | string | 词表类别 |
| `id` | int | 词条 ID |

**请求体：** 无

**成功响应 (200)：**
```json
{
  "deleted": true
}
```

**错误码：**
- `404`：词条不存在 — `{"error": "Entry not found"}`
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

### `POST /api/dict/seed`

初始化内置别名映射到数据库。幂等操作，已存在的标准名称不会被重复创建。仅管理员可调用。

**权限：** `admin`

**请求体：** 无

**成功响应 (201)：**
```json
{
  "seeded": 15
}
```

如果所有映射已存在：
```json
{
  "seeded": 0
}
```
（此时返回 200）

**错误码：**
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证
