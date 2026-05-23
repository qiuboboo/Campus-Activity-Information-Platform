# 数据源接口 API

数据源的增删改查、手动触发抓取、查看抓取日志。安全约束（URL 白名单、内网拦截、敏感信息掩码等）见[模块设计.md](模块设计.md)。

---

## `GET /api/data-sources`

获取所有数据源配置列表。

**权限：** 需 JWT 认证（`@jwt_required()`）

**查询参数：** 无

**成功响应（200）：**

```json
{
  "items": [
    {
      "id": 1,
      "name": "中山大学新闻网-一线动态",
      "base_url": "https://www.sysu.edu.cn/news/yxdt.htm",
      "list_selector": "a.title",
      "content_selector": "div.v_news_content",
      "enabled": true,
      "crawl_mode": "basic",
      "source_level": "official",
      "owner": "admin",
      "notes": "爬取中山大学新闻网一线动态栏目",
      "allowed_domains": "sysu.edu.cn",
      "request_interval": 3,
      "last_success_at": "2026-05-23T10:00:00",
      "last_failure_at": null,
      "last_error_message": null,
      "created_at": "2026-05-20T08:00:00",
      "updated_at": "2026-05-23T10:00:00"
    }
  ]
}
```

**错误码：**

| 状态码 | 说明 |
|--------|------|
| 401 | 未提供或无效的 JWT |

---

## `POST /api/data-sources`

创建新的数据源配置。

**权限：** 需 admin 角色（`@roles_required("admin")`）

**请求体：**

```json
{
  "name": "中山大学药学院-学术讲座",
  "base_url": "https://sps.sysu.edu.cn/event",
  "list_selector": "ul.event-list li",
  "content_selector": "article",
  "crawl_mode": "basic",
  "enabled": true,
  "source_level": "official",
  "owner": "教务处",
  "notes": "药学院学术讲座列表",
  "allowed_domains": "sps.sysu.edu.cn",
  "request_interval": 3
}
```

**请求字段说明：**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | 是 | — | 数据源名称 |
| `base_url` | string | 是 | — | 目标 URL，必须以 `http://` 或 `https://` 开头 |
| `list_selector` | string | 否 | `null` | 列表页 CSS 选择器 |
| `content_selector` | string | 否 | `null` | 内容页 CSS 选择器 |
| `crawl_mode` | string | 否 | `"basic"` | 爬取模式：`basic` / `mcp` / `weixin` |
| `enabled` | bool | 否 | `true` | 是否启用 |
| `source_level` | string | 否 | `"external"` | 来源级别：`official` / `internal` / `external` |
| `owner` | string | 否 | `null` | 负责人 |
| `notes` | string | 否 | `null` | 备注说明 |
| `allowed_domains` | string | 否 | `null` | 允许抓取的域名白名单，逗号分隔 |
| `request_interval` | int | 否 | `2` | 请求间隔（秒） |

**成功响应（201）：**

```json
{
  "id": 2,
  "name": "中山大学药学院-学术讲座",
  "base_url": "https://sps.sysu.edu.cn/event",
  "list_selector": "ul.event-list li",
  "content_selector": "article",
  "enabled": true,
  "crawl_mode": "basic",
  "source_level": "official",
  "owner": "教务处",
  "notes": "药学院学术讲座列表",
  "allowed_domains": "sps.sysu.edu.cn",
  "request_interval": 3,
  "last_success_at": null,
  "last_failure_at": null,
  "last_error_message": null,
  "created_at": "2026-05-24T12:00:00",
  "updated_at": "2026-05-24T12:00:00"
}
```

**错误码：**

| 状态码 | 说明 |
|--------|------|
| 400 | `name` 或 `base_url` 缺失，或 `crawl_mode` / `source_level` 不合法，或 `base_url` 格式错误 |
| 401 | 未提供或无效的 JWT |
| 403 | 当前用户非 admin 角色 |

---

## `GET /api/data-sources/{id}`

获取单个数据源的详细信息。

**权限：** 需 JWT 认证（`@jwt_required()`）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 数据源 ID |

**成功响应（200）：**

响应结构与 `POST` 创建成功时相同（单条数据源 JSON 对象）。

**错误码：**

| 状态码 | 说明 |
|--------|------|
| 401 | 未提供或无效的 JWT |
| 404 | 数据源不存在（`{"error": "Data source not found"}`） |

---

## `PUT /api/data-sources/{id}`

更新数据源配置。所有字段均为可选，只传需要修改的字段。

**权限：** 需 admin 角色（`@roles_required("admin")`）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 数据源 ID |

**请求体：**

```json
{
  "name": "更新后的数据源名称",
  "enabled": false,
  "request_interval": 5
}
```

请求字段与 `POST /api/data-sources` 相同，全部可选。

**成功响应（200）：**

返回更新后的完整数据源 JSON 对象。

**错误码：**

| 状态码 | 说明 |
|--------|------|
| 400 | `crawl_mode` 或 `source_level` 值不合法，或 `base_url` 格式错误 |
| 401 | 未提供或无效的 JWT |
| 403 | 当前用户非 admin 角色 |
| 404 | 数据源不存在 |

---

## `DELETE /api/data-sources/{id}`

删除数据源及其关联的抓取日志（级联删除）。

**权限：** 需 admin 角色（`@roles_required("admin")`）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 数据源 ID |

**成功响应（200）：**

```json
{
  "success": true,
  "message": "Data source deleted"
}
```

**错误码：**

| 状态码 | 说明 |
|--------|------|
| 401 | 未提供或无效的 JWT |
| 403 | 当前用户非 admin 角色 |
| 404 | 数据源不存在 |

---

## `POST /api/data-sources/{id}/crawl`

手动触发抓取任务。

**权限：** 需 admin 角色（`@roles_required("admin")`）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 数据源 ID |

**请求体：**

```json
{
  "sync": false
}
```

**请求字段说明：**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `sync` | bool | 否 | `false` | `true` 时同步执行（调试用）；`false` 时异步提交 Celery 任务 |

**行为说明：**

- **默认（异步）**：通过 Celery Worker 后台执行，返回 202
- **同步模式（`sync=true`）**：直接在当前进程中执行，返回 200
- **微信模式（`crawl_mode=weixin`）**：始终同步执行，通过搜狗微信搜索关键词（`base_url` 作查询词），结果直接创建为 Poster 草稿
- **MCP 模式（`crawl_mode=mcp`）**：始终同步执行

**异步响应（202）：**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status_url": "/api/tasks/550e8400-e29b-41d4-a716-446655440000"
}
```

**同步响应（200，basic/mcp 模式）：**

```json
{
  "success": true,
  "message": "抓取完成",
  "pages_found": 5,
  "pages_succeeded": 5,
  "pages_failed": 0,
  "drafts_created": 3
}
```

**同步响应（200，weixin 模式）：**

```json
{
  "success": true,
  "message": "微信搜索完成，找到 10 条，新建 4 条"
}
```

**错误码：**

| 状态码 | 说明 |
|--------|------|
| 401 | 未提供或无效的 JWT |
| 403 | 当前用户非 admin 角色 |
| 404 | 数据源不存在 |
| 500 | 同步抓取执行失败（`{"error": "Crawl failed"}`） |

---

## `GET /api/data-sources/{id}/logs`

查看指定数据源的抓取日志列表。

**权限：** 需 JWT 认证（`@jwt_required()`）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 数据源 ID |

**成功响应（200）：**

```json
{
  "items": [
    {
      "id": 100,
      "data_source_id": 1,
      "status": "completed",
      "message": "抓取完成，共处理 10 页",
      "started_at": "2026-05-23T10:00:00",
      "finished_at": "2026-05-23T10:05:30",
      "pages_found": 10,
      "pages_succeeded": 8,
      "pages_failed": 2,
      "duplicates_skipped": 0,
      "drafts_created": 5,
      "average_quality_score": 85.5
    }
  ]
}
```

**`status` 可能取值：** `running` / `completed` / `failed` / `partial`

**错误码：**

| 状态码 | 说明 |
|--------|------|
| 401 | 未提供或无效的 JWT |
| 404 | 数据源不存在 |
