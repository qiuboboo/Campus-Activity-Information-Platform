# 质量评分、去重与审计模块 API

---

## 审计日志

### `GET /api/audit-logs`

查看审计日志列表，支持按操作人、操作类型、目标类型过滤和分页。仅管理员可调用。

**权限：** `admin`

**查询参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `actor_id` | int | 否 | — | 按操作人用户 ID 过滤 |
| `action` | string | 否 | — | 按操作类型过滤（如 `"review_approve"`、`"review_reject"`、`"batch_review"`、`"knowledge_rebuild"`、`"source_merge"`） |
| `target_type` | string | 否 | — | 按目标对象类型过滤（如 `"poster"`、`"datasource"`） |
| `page` | int | 否 | `1` | 页码 |
| `per_page` | int | 否 | `20` | 每页条数，最大 `100` |

**成功响应 (200)：**
```json
{
  "items": [
    {
      "id": 1,
      "actor_id": 1,
      "action": "review_approve",
      "target_type": "poster",
      "target_id": 42,
      "summary": "Approved poster '科技节'",
      "metadata_json": "{\"review_comment\": \"内容符合规范\"}",
      "created_at": "2026-05-24T10:00:00"
    },
    {
      "id": 2,
      "actor_id": 1,
      "action": "knowledge_rebuild",
      "target_type": null,
      "target_id": null,
      "summary": "Rebuilt knowledge graph",
      "metadata_json": null,
      "created_at": "2026-05-24T11:00:00"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 2
}
```

**错误码：**
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

## 数据导出

### `GET /api/export/posters.json`

导出所有海报数据为 JSON（不含 `raw_text` 和 `password_hash`）。仅管理员可调用。

**权限：** `admin`

**查询参数：** 无

**成功响应 (200)：**
```json
{
  "count": 150,
  "items": [
    {
      "id": 1,
      "title": "校园科技文化节",
      "summary": "一年一度的科技文化节...",
      "event_time": "2026-05-10T19:00:00",
      "location": "大礼堂",
      "organizer": "校团委",
      "status": "published",
      "source_type": "manual",
      "source_url": "https://example.edu.cn/event",
      "created_by": 1,
      "duplicate_group_key": null,
      "source_fingerprint": "abc123...",
      "quality_score": 95,
      "quality_notes": "官方来源加分",
      "tags": "科技,校园文化",
      "activity_type": "其他",
      "created_at": "2026-05-01T00:00:00",
      "updated_at": "2026-05-02T00:00:00"
    }
  ]
}
```

**字段排除：** `raw_text` 和 `password_hash`（海报模型不存在此字段，但 API 做了安全性移除）被排除以减小导出体积。

**错误码：**
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

### `GET /api/export/knowledge.json`

导出所有知识节点为 JSON。仅管理员可调用。

**权限：** `admin`

**查询参数：** 无

**成功响应 (200)：**
```json
{
  "count": 50,
  "items": [
    {
      "id": 1,
      "name": "大礼堂",
      "alias": null,
      "node_type": "place",
      "description": "校内主要活动举办场地",
      "source_url": null,
      "embedding": null,
      "created_at": "2026-01-01T00:00:00",
      "updated_at": "2026-05-01T00:00:00"
    }
  ]
}
```

**错误码：**
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

### `GET /api/export/crawl-report.json`

导出最近的抓取日志统计数据（最近 100 条）。仅管理员可调用。

**权限：** `admin`

**查询参数：** 无

**成功响应 (200)：**
```json
{
  "count": 10,
  "items": [
    {
      "id": 1,
      "data_source_id": 2,
      "status": "success",
      "message": null,
      "started_at": "2026-05-24T08:00:00",
      "finished_at": "2026-05-24T08:05:00",
      "pages_found": 20,
      "pages_succeeded": 18,
      "pages_failed": 2,
      "duplicates_skipped": 3,
      "drafts_created": 15,
      "average_quality_score": 82.5,
      "created_at": "2026-05-24T08:05:00",
      "updated_at": "2026-05-24T08:05:00"
    }
  ]
}
```

**错误码：**
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

### `GET /api/demo/summary`

获取平台数据汇总统计。仅管理员可调用。

**权限：** `admin`

**查询参数：** 无

**成功响应 (200)：**
```json
{
  "posters": {
    "total": 150,
    "published": 120,
    "draft": 20,
    "rejected": 10
  },
  "knowledge_nodes": 50,
  "poster_links": 200,
  "data_sources": 5,
  "last_crawl": {
    "id": 1,
    "data_source_id": 2,
    "status": "success",
    "pages_found": 20,
    "pages_succeeded": 18,
    "pages_failed": 2,
    "duplicates_skipped": 3,
    "drafts_created": 15,
    "average_quality_score": 82.5,
    "started_at": "2026-05-24T08:00:00",
    "finished_at": "2026-05-24T08:05:00"
  }
}
```

`last_crawl` 为 `null` 时表示尚无抓取记录。

**错误码：**
- `403`：非 admin 用户 — `{"message": "permission denied"}`
- `401`：未认证

---

## 系统接口

### `GET /api/health`

健康检查。公开接口，无需认证。返回数据库和 Redis 连接状态。

**权限：** 公开（无需 JWT）

**查询参数：** 无

**成功响应 (200)——全部正常：**
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "service": "campus-activity-backend",
  "timestamp": "2026-05-24T12:00:00+00:00"
}
```

**成功响应 (200)——部分降级（如数据库不可用）：**
```json
{
  "status": "degraded",
  "database": "unavailable",
  "redis": "ok",
  "service": "campus-activity-backend",
  "timestamp": "2026-05-24T12:00:00+00:00"
}
```

**错误码：** 无（始终返回 200）

---

### `GET /api/tasks/{task_id}`

查询 Celery 异步任务的状态和结果。

**权限：** 需 JWT 认证（任意角色）

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | Celery 任务 ID（UUID 字符串） |

**成功响应 (200)——任务进行中：**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "PENDING",
  "result": null,
  "error": null
}
```

**成功响应 (200)——任务成功：**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "SUCCESS",
  "result": { "posters_created": 15 },
  "error": null
}
```

**成功响应 (200)——任务失败：**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "FAILURE",
  "result": null,
  "error": "Connection timeout"
}
```

**错误码：**
- `401`：未认证

---

## 去重查询（备查）

去重检查通过海报 API 的子接口完成。

### `GET /api/posters/{id}/duplicates`

查看指定海报的疑似重复项。（此端点在 posters.py 模块中实现，此处仅做引用。）

**权限：** 需 JWT 认证

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**成功响应 (200)：**
```json
{
  "poster_id": 42,
  "duplicates": [
    {
      "id": 15,
      "title": "校园科技文化节",
      "similarity": "source_fingerprint"
    }
  ],
  "duplicate_group_key": "abc123..."
}
```
