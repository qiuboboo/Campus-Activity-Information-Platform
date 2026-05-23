# 搜索接口 API

本文档列举搜索模块的全部 HTTP 端点。详细的字段类型、枚举取值、null 语义和完整 JSON 示例见[接口契约.md](接口契约.md)。

---

## `GET /api/search/internal`

在平台内部知识库中执行检索，同时搜索海报（Poster）和知识节点（KnowledgeNode）。

**权限：** 需 JWT 认证（`@jwt_required()`）

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 是 | — | 搜索关键词；为空时直接返回空结果（200） |
| `sort` | string | 否 | `relevance` | 排序字段：`relevance` / `created_at` / `title` / `event_time` |
| `order` | string | 否 | `desc` | 排序方向：`asc` / `desc` |
| `page` | int | 否 | `1` | 页码，最小值 1（当前实现限制 max 20 条，暂未使用分页偏移） |
| `per_page` | int | 否 | `20` | 每页条数，最大值 50（当前实现固定 limit 20） |

**检索范围：**

- **海报**：匹配 `title`、`summary`、`raw_text`、`location`、`organizer` 字段
- **知识节点**：匹配 `name`、`description` 字段

**成功响应（200）：**

```json
{
  "items": [
    {
      "hit_type": "poster",
      "item": {
        "id": 1,
        "title": "AI 创新应用讲座",
        "summary": "讲座将介绍 AI 前沿技术在校园中的应用",
        "event_time": "2026-05-10T15:00:00",
        "location": "大学生活动中心大礼堂",
        "organizer": "计算机学院",
        "status": "published",
        "source_type": "manual",
        "source_url": null,
        "review_comment": null,
        "created_by": 1,
        "created_at": "2026-05-10T10:00:00",
        "updated_at": "2026-05-10T12:00:00",
        "duplicate_group_key": null,
        "source_fingerprint": null,
        "quality_score": null,
        "quality_notes": null,
        "tags": null,
        "activity_type": null,
        "content_html": "<div>...</div>",
        "last_crawled_at": null,
        "embedding": null
      }
    },
    {
      "hit_type": "knowledge_node",
      "item": {
        "id": 10,
        "name": "大学生活动中心大礼堂",
        "alias": null,
        "node_type": "location",
        "description": null,
        "source_url": null,
        "created_at": "2026-05-10T10:00:00",
        "updated_at": "2026-05-10T12:00:00",
        "embedding": null
      }
    }
  ],
  "query": "讲座",
  "search_mode": "fulltext",
  "sort": "relevance",
  "order": "desc"
}
```

- `search_mode`：`"fulltext"`（始终可用）或 `"vector"`（当 `EMBEDDING_ENABLED=true` 且 `sort=relevance` 时启用）
- `sort` / `order`：请求指定的排序参数；当查询为空时可能缺失

**空查询响应（200）：**

```json
{
  "items": [],
  "query": ""
}
```

**错误码：**

| 状态码 | 说明 |
|--------|------|
| 401 | 未提供或无效的 JWT |
| 422 | JWT 格式有误或已过期（Flask-JWT-Extended 默认） |

---

## `GET /api/search/external`

通过多引擎搜索服务（SearXNG 聚合 Google、Bing、DuckDuckGo、百度 + 搜狗微信搜索）获取外部活动信息。支持 LLM 兜底。

**权限：** 需 JWT 认证（`@jwt_required()`）

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 是 | — | 搜索关键词；为空返回 400 |
| `sources` | string | 否 | `web,sogou` | 搜索源，逗号分隔。可选值：`web`（搜索引擎）、`sogou`（搜狗微信）、`llm`（LLM 兜底） |

- `sources` 不传时默认使用 `web`（Google、Bing、DuckDuckGo、百度）+ `sogou`（搜狗微信）
- `sources=llm` 仅当多搜索引擎无结果且 `LLM_API_KEY` 已配置时生效
- `sources=web` 等价于请求 Google、Bing、DuckDuckGo、百度四个引擎

**成功响应（200）：**

```json
{
  "query": "校园科技节",
  "results": [
    {
      "title": "关于举办2026年校园科技节的通知",
      "summary": "2026年校园科技节将于5月10日开幕...",
      "source": "baidu",
      "url": "https://www.sysu.edu.cn/news/123"
    },
    {
      "title": "科技节系列活动预告",
      "summary": "科技节期间将举办多场讲座和竞赛...",
      "source": "google",
      "url": "https://www.sysu.edu.cn/news/456"
    },
    {
      "title": "科技节",
      "summary": "中山大学2026年科技节活动安排",
      "source": "bing",
      "url": "https://cn.bing.com/search?q=..."
    }
  ],
  "count": 3,
  "source": "multi",
  "error": null
}
```

**空结果响应（200）：**

```json
{
  "query": "xyz_unknown_abc",
  "results": [],
  "count": 0,
  "source": "multi",
  "error": null
}
```

**所有引擎不可用（200）：**

```json
{
  "query": "讲座",
  "results": [],
  "count": 0,
  "source": "multi",
  "error": "All search engines returned no results"
}
```

**错误码：**

| 状态码 | 说明 |
|--------|------|
| 400 | 缺少 `q` 参数（`{"error": "query parameter 'q' is required"}`） |
| 401 | 未提供或无效的 JWT |
| 422 | JWT 格式有误或已过期 |

`error` 字段的取值说明见[接口契约.md](接口契约.md#24-error-取值说明)。
