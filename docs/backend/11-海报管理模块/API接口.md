# 海报管理接口 API

所有海报接口统一注册在 `/api/posters` 路径下。需要认证的接口统一验证 JWT，角色控制通过 `@roles_required()` 装饰器实现。

**海报状态流转：**
```
draft → pending_review → published
                        → rejected (可返回 draft 修改后重新提交)
```

---

## `GET /api/posters`

分页获取海报列表，支持关键词和状态过滤。

**权限：** 需 JWT 认证

**查询参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 否 | — | 关键词搜索，匹配 title / summary / raw_text |
| `status` | string | 否 | — | 按状态过滤，可选值：`draft` / `pending_review` / `published` / `rejected` |
| `page` | int | 否 | 1 | 页码 |
| `per_page` | int | 否 | 配置默认值（≤50） | 每页条数 |

**成功响应 (200)：**
```json
{
  "items": [
    {
      "id": 1,
      "title": "2026 校园科技文化节开幕式",
      "raw_text": "2026 校园科技文化节将于 2026-05-10 19:00 在大学生活动中心大礼堂举行。",
      "summary": "校园科技文化节开幕式，面向全校师生开放。",
      "event_time": "2026-05-10T19:00:00",
      "location": "大学生活动中心大礼堂",
      "organizer": "校团委",
      "status": "draft",
      "source_type": "manual",
      "source_url": "https://example.edu.cn/tech-culture",
      "review_comment": null,
      "created_by": 1,
      "created_at": "2026-05-21T09:45:41",
      "updated_at": "2026-05-21T09:45:41",
      "duplicate_group_key": null,
      "source_fingerprint": null,
      "quality_score": null,
      "quality_notes": null,
      "tags": null,
      "activity_type": null,
      "content_html": null,
      "last_crawled_at": null,
      "embedding": null
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 1
}
```

**错误码：**
- `401`：未提供 JWT

---

## `POST /api/posters`

创建海报草稿或直接发布海报。

**权限：** `publisher` 或 `admin`

**请求体：**
```json
{
  "raw_text": "2026 校园科技文化节将于 2026-05-10 19:00 在大学生活动中心大礼堂举行。",
  "title": "2026 校园科技文化节开幕式",
  "summary": "校园科技文化节开幕式",
  "event_time": "2026-05-10T19:00:00",
  "location": "大学生活动中心大礼堂",
  "organizer": "校团委",
  "activity_type": "开幕式",
  "source_type": "manual",
  "source_url": "https://example.edu.cn/events"
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `raw_text` | string | **是** | 活动原始文本（不可为空） |
| `title` | string | 否 | 自动从 raw_text 第一行提取，最长 80 字符 |
| `summary` | string | 否 | 自动从 raw_text 提取，最长 120 字符 |
| `event_time` | string | 否 | ISO 8601 格式（如 `2026-05-10T19:00:00`） |
| `location` | string | 否 | 活动地点 |
| `organizer` | string | 否 | 主办方 |
| `activity_type` | string | 否 | 活动类型 |
| `status` | string | 否 | 默认为 `draft`，传入 `published` 可直接发布 |
| `source_type` | string | 否 | 默认为 `manual` |
| `source_url` | string | 否 | 来源 URL |

**成功响应 (201)：**
```json
{
  "item": {
    "id": 1,
    "title": "2026 校园科技文化节开幕式",
    "raw_text": "2026 校园科技文化节将于 2026-05-10 19:00 在大学生活动中心大礼堂举行。",
    "summary": "校园科技文化节开幕式",
    "event_time": "2026-05-10T19:00:00",
    "location": "大学生活动中心大礼堂",
    "organizer": "校团委",
    "status": "draft",
    "source_type": "manual",
    "source_url": "https://example.edu.cn/events",
    "review_comment": null,
    "created_by": 1,
    "created_at": "2026-05-21T09:45:41",
    "updated_at": "2026-05-21T09:45:41",
    "duplicate_group_key": null,
    "source_fingerprint": null,
    "quality_score": null,
    "quality_notes": null,
    "tags": null,
    "activity_type": "开幕式",
    "content_html": "<div class=\"activity-poster\">\\n  <h2 class=\"poster-title\">...</h2>\\n</div>",
    "last_crawled_at": null,
    "embedding": null
  }
}
```

**附带操作：**
- 如果 `status` 为 `published`，自动触发知识节点重建和推送通知

**错误码：**
- `400`：`raw_text is required`（缺少原始文本）
- `401`：未提供 JWT
- `403`：角色非 `publisher` 或 `admin`

---

## `GET /api/posters/{id}`

获取单个海报详情。

**权限：** 需 JWT 认证

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**成功响应 (200)：**
```json
{
  "item": { "id": 1, "title": "...", ... }
}
```

**错误码：**
- `401`：未提供 JWT
- `404`：海报不存在

---

## `PUT /api/posters/{id}`

编辑海报内容。当标题、摘要、时间、地点、主办方等字段变动时，自动重新生成 HTML 内容。如果海报状态为 `published`，自动触发知识节点重建和推送通知。

**权限：** `publisher` 或 `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**请求体（支持部分更新）：**
```json
{
  "title": "更新后的标题",
  "summary": "更新后的摘要",
  "location": "新地点",
  "event_time": "2026-06-01T14:00:00",
  "organizer": "新主办方",
  "activity_type": "讲座",
  "source_type": "crawl",
  "source_url": "https://example.edu.cn/new-event"
}
```

**字段说明：**
| 字段 | 类型 | 说明 |
|------|------|------|
| `raw_text` | string | 不可设为空字符串（可为 `null` 不传） |
| 其他字段 | 同创建接口 | 不传的字段保持原值（fallback） |

**成功响应 (200)：**
```json
{
  "item": { "id": 1, "title": "更新后的标题", ... }
}
```

**错误码：**
- `400`：`raw_text cannot be empty`（显式设为空字符串时）
- `401`：未提供 JWT
- `403`：角色非 `publisher` 或 `admin`
- `404`：海报不存在

---

## `POST /api/posters/{id}/submit`

用户将草稿提交审核。状态从 `draft` 变更为 `pending_review`。

**权限：** `publisher` 或 `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**请求体：** 无需请求体

**成功响应 (200)：**
```json
{
  "item": {
    "id": 1,
    "title": "2026 校园科技文化节开幕式",
    "status": "pending_review"
  }
}
```

**附带操作：** 创建审核日志（action=`submit`）

**错误码：**
- `400`：`cannot submit poster with status '...'`（非 draft 状态不可提交）
- `401`：未提供 JWT
- `403`：角色非 `publisher` 或 `admin`
- `404`：海报不存在

---

## `POST /api/posters/{id}/review`

管理员审核海报，通过或驳回。可审核 `draft` 和 `pending_review` 状态的海报。

**权限：** `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**请求体：**
```json
{
  "action": "approve",
  "comment": "内容符合要求，审核通过"
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | `approve`（发布）或 `reject`（驳回） |
| `comment` | string | 否 | 审核意见（驳回时建议填写） |

**成功响应 (200) — 通过：**
```json
{
  "item": {
    "id": 1,
    "title": "2026 校园科技文化节开幕式",
    "status": "published",
    "review_comment": "内容符合要求，审核通过"
  }
}
```

**成功响应 (200) — 驳回：**
```json
{
  "item": {
    "id": 1,
    "title": "2026 校园科技文化节开幕式",
    "status": "rejected",
    "review_comment": "需要补充活动时间"
  }
}
```

**附带操作：**
- 审核通过时：自动触发知识节点重建和推送通知
- 创建审核日志（action=`review_approve` 或 `review_reject`）

**错误码：**
- `400`：
  - `action must be approve or reject`（操作不合法）
  - `cannot review poster with status '...'`（状态不属于 `pending_review` 或 `draft`）
- `401`：未提供 JWT
- `403`：角色非 `admin`
- `404`：海报不存在

---

## `GET /api/posters/review-queue`

获取待审核海报列表。默认返回 `pending_review`、`draft`、`rejected` 状态的海报。

**权限：** `admin`

**查询参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `status` | string | 否 | — | 按状态过滤，不传则返回 pending_review + draft + rejected |
| `source_type` | string | 否 | — | 按来源类型过滤 |
| `duplicate_group_key` | string | 否 | — | 按重复分组键过滤 |
| `sort_by` | string | 否 | `-created_at` | 排序字段，加 `-` 前缀表示降序 |
| `page` | int | 否 | 1 | 页码 |
| `per_page` | int | 否 | 20 | 每页条数（最大 100） |

**成功响应 (200)：**
```json
{
  "items": [ { "id": 1, "title": "...", "status": "pending_review", ... } ],
  "page": 1,
  "per_page": 20,
  "total": 5
}
```

**错误码：**
- `401`：未提供 JWT
- `403`：角色非 `admin`

---

## `POST /api/posters/bulk-review`

批量审核多个海报。逐个处理，返回成功和失败列表。

**权限：** `admin`

**请求体：**
```json
{
  "poster_ids": [1, 2, 3],
  "action": "approve",
  "comment": "批量审核通过"
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `poster_ids` | int[] | 是 | 待审核的海报 ID 列表 |
| `action` | string | 是 | `approve` 或 `reject` |
| `comment` | string | 否 | 审核意见，应用于所有海报 |

**成功响应 (200)：**
```json
{
  "succeeded": [
    { "id": 1, "status": "published" },
    { "id": 2, "status": "published" }
  ],
  "failed": [
    { "id": 3, "error": "not found" }
  ]
}
```

**错误码：**
- `400`：
  - `poster_ids is required`（缺少海报 ID 列表）
  - `action must be approve or reject`（操作不合法）
- `401`：未提供 JWT
- `403`：角色非 `admin`

---

## `GET /api/posters/{id}/duplicates`

查询指定海报的可能重复项。检查依据：相同的 `duplicate_group_key` 或相同的 `source_fingerprint`。

**权限：** `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**成功响应 (200)：**
```json
{
  "poster": { "id": 1, "title": "...", "duplicate_group_key": "abc123", "source_fingerprint": "def456" },
  "duplicates": [
    { "id": 2, "title": "相似活动", ... }
  ],
  "count": 1
}
```

**错误码：**
- `401`：未提供 JWT
- `403`：角色非 `admin`
- `404`：海报不存在

---

## `POST /api/posters/{id}/merge-source`

将来源海报合并到当前海报。合并后来源海报被删除，当前海报的知识节点被重建。

**权限：** `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 目标海报（保留）ID |

**请求体：**
```json
{
  "source_poster_id": 2
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_poster_id` | int | 是 | 来源海报（将被删除）ID |

**成功响应 (200)：**
```json
{
  "item": { "id": 1, "title": "主海报" },
  "merged": {
    "id": 2,
    "title": "重复来源",
    "urls": ["https://example.edu.cn/dup"]
  }
}
```

**附带操作：**
- 来源海报被删除（级联删除关联的 PosterNode / PosterLink）
- 目标海报知识节点重建
- 创建审核日志（action=`merge_source`）

**错误码：**
- `400`：`source_poster_id is required`（缺少来源海报 ID）
- `401`：未提供 JWT
- `403`：角色非 `admin`
- `404`：海报不存在 或 来源海报不存在（`Source poster not found`）

---

## `POST /api/posters/{id}/rebuild-knowledge

重新生成指定海报的知识节点关联和海报间关系。

**权限：** `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**请求体：** 无需请求体

**成功响应 (200)：**
```json
{
  "item": { "id": 1, "title": "..." },
  "nodes_created": 5,
  "links_created": 3
}
```

**附带操作：**
- 删除该海报的旧知识节点关联和链接
- 重新执行规则抽取和建边
- 创建审核日志（action=`rebuild_knowledge`）

**错误码：**
- `401`：未提供 JWT
- `403`：角色非 `admin`
- `404`：海报不存在

---

## `POST /api/posters/{id}/ai-enrich`

调用 AI 对海报进行摘要、分类、标签等智能增强。

**权限：** `admin`

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**请求体：** 无需请求体

**成功响应 (200)：**
```json
{
  "item": { "id": 1, "title": "..." },
  "ai_result": {
    "summary": "AI 生成的摘要...",
    "tags": ["人工智能", "讲座", "科技创新"],
    "keywords": ["AI", "机器学习", "应用"]
  }
}
```

**附带操作：**
- 调用 `ai_service.enrich_poster()`
- 如果 LLM 可用，自动更新 poster 内容并重新生成 HTML

**错误码：**
- `400`：`Enrichment failed (LLM unavailable or poster not found)`（LLM 不可用或海报不存在）
- `401`：未提供 JWT
- `403`：角色非 `admin`
- `404`：海报不存在
