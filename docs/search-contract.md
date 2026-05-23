# 搜索 API 接口契约

## 概述

本文档定义搜索模块的 HTTP 接口请求/响应结构，作为前后端联调的依据。所有字段类型、null 语义和错误场景均按此文档对齐。

---

## 1. 内部搜索 `GET /api/search/internal?q=...`

### 1.1 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 是 | — | 搜索关键词；为空时直接返回空结果（200） |
| `page` | int | 否 | `1` | 页码，最小值 1 |
| `per_page` | int | 否 | `20` | 每页条数，最大值 50 |

### 1.2 返回结构

```json
{
  "items": [
    {
      "hit_type": "poster",
      "item": { "... 见 1.3 ..." }
    },
    {
      "hit_type": "knowledge_node",
      "item": { "... 见 1.3 ..." }
    }
  ],
  "query": "搜索词",
  "search_mode": "fulltext"
}
```

### 1.3 `items[].hit_type` 枚举

| 取值 | 说明 | `item` 包含的字段 |
|------|------|-------------------|
| `poster` | 活动海报 | 见 [Poster.to_dict()](../backend/app/models.py#L104) 全部字段 |
| `knowledge_node` | 知识节点 | 见 [KnowledgeNode.to_dict()](../backend/app/models.py#L154) 全部字段 |

### 1.4 `search_mode` 取值

| 取值 | 说明 | 启用条件 |
|------|------|----------|
| `fulltext` | PostgreSQL `LIKE` 全文检索 | 始终可用 |
| `vector` | pgvector 语义向量检索 | `EMBEDDING_ENABLED=true` 且 pgvector 扩展已安装 |

### 1.5 Null 语义

- `items`：空结果时为 `[]`，不会是 `null` 或缺失
- `item` 中的标量字段：`null` 表示该字段未设置（如 draft 状态的 `event_time`）
- `query`：始终为 string，不会为 `null`
- `search_mode`：当查询为空时可能缺失，否则始终有值

### 1.6 场景示例

**正常结果：**
```
GET /api/search/internal?q=讲座
→ 200
{
  "items": [
    {
      "hit_type": "poster",
      "item": { "id": 1, "title": "AI 创新应用讲座", "summary": "...", "event_time": "2026-05-10T15:00:00", "location": "大学生活动中心大礼堂", "organizer": "计算机学院", "status": "published", "source_type": "manual", "source_url": null, "review_comment": null, "created_by": 1, "created_at": "2026-05-10T10:00:00", "updated_at": "2026-05-10T12:00:00", "duplicate_group_key": null, "source_fingerprint": null, "quality_score": null, "quality_notes": null, "tags": null, "activity_type": null, "content_html": "<div>...</div>", "last_crawled_at": null, "embedding": null }
    },
    {
      "hit_type": "knowledge_node",
      "item": { "id": 10, "name": "大学生活动中心大礼堂", "alias": null, "node_type": "location", "description": null, "source_url": null, "created_at": "2026-05-10T10:00:00", "updated_at": "2026-05-10T12:00:00", "embedding": null }
    }
  ],
  "query": "讲座",
  "search_mode": "fulltext"
}
```

**空结果：**
```
GET /api/search/internal?q=zzz_no_match_xyz
→ 200
{
  "items": [],
  "query": "zzz_no_match_xyz",
  "search_mode": "fulltext"
}
```

**空查询（直出空）：**
```
GET /api/search/internal?q=
→ 200
{
  "items": [],
  "query": ""
}
```

**未认证：**
```
GET /api/search/internal?q=讲座
→ 401
{
  "error": "Unauthorized",
  "message": "Missing Authorization Header",
  "code": 401
}
```

---

## 2. 外部搜索 `GET /api/search/external?q=...`

### 2.1 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 是 | — | 搜索关键词；为空返回 400 |

### 2.2 返回结构

```json
{
  "query": "搜索词",
  "results": [
    {
      "title": "结果标题",
      "summary": "结果摘要",
      "source": "来源名称",
      "url": "https://example.com/article"
    }
  ],
  "count": 1,
  "source": "llm",
  "error": null
}
```

### 2.3 字段说明

| 字段 | 类型 | 必含 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 原始查询词 |
| `results` | `list[dict]` | 是 | 结果数组；无结果时为 `[]`，不会是 `null` 或缺失 |
| `results[].title` | string | 是 | 结果标题 |
| `results[].summary` | string | 是 | 结果摘要 |
| `results[].source` | string | 是 | 信息来源名称（如"中山大学官网"） |
| `results[].url` | string\|null | 否 | 信息来源链接；LLM 可能无法提供，此时为 `null` |
| `count` | int | 是 | 结果数量，等于 `len(results)` |
| `source` | string | 是 | 固定为 `"llm"`（保留扩展，后续可支持其他外部搜索源） |
| `error` | string\|null | 否 | 正常时为 `null`；异常时返回人类可读的错误描述 |

### 2.4 error 取值说明

| `error` 值 | 含义 | 前端建议表现 |
|------------|------|-------------|
| `null` | 调用成功 | 正常展示 `results` |
| `"LLM service not configured"` | 后端未配置 LLM API Key | 显示"搜索服务未配置"提示 |
| `"LLM service unavailable"` | LLM 调用失败（网络/超时） | 显示"搜索服务暂时不可用"提示 |
| `"LLM returned invalid response format"` | LLM 返回了非预期的数据格式 | 显示"搜索结果异常"提示 |

### 2.5 场景示例

**正常结果：**
```
GET /api/search/external?q=校园科技节
→ 200
{
  "query": "校园科技节",
  "results": [
    { "title": "2026 校园科技节开幕式", "summary": "2026 年校园科技节将于 5 月 10 日开幕...", "source": "中山大学官网", "url": "https://www.sysu.edu.cn/news/123" },
    { "title": "科技节系列活动预告", "summary": "科技节期间将举办多场讲座和竞赛...", "source": "中山大学团委", "url": null }
  ],
  "count": 2,
  "source": "llm",
  "error": null
}
```

**正常空结果（LLM 真的没找到）：**
```
GET /api/search/external?q=xyz_unknown_abc
→ 200
{
  "query": "xyz_unknown_abc",
  "results": [],
  "count": 0,
  "source": "llm",
  "error": null
}
```

**LLM 服务不可用：**
```
GET /api/search/external?q=讲座
→ 200
{
  "query": "讲座",
  "results": [],
  "count": 0,
  "source": "llm",
  "error": "LLM service unavailable"
}
```

**缺少查询词：**
```
GET /api/search/external?q=
→ 400
{
  "error": "query parameter 'q' is required"
}
```

**未认证：**
```
GET /api/search/external?q=讲座
→ 401
{
  "error": "Unauthorized",
  "message": "Missing Authorization Header",
  "code": 401
}
```

---

## 3. 版本记录

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0 | 2026-05-24 | 初版，冻结 Internal / External 搜索接口契约 |
