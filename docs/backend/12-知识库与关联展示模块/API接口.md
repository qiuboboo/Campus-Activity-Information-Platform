# 知识库与关联展示 API

接口分布在两个蓝图中：
- `/api/knowledge/*` — 知识节点管理（`knowledge_bp`）
- `/api/posters/{id}/related` — 关联展示（`posters_bp`，与海报管理模块共享路由）

---

## `GET /api/knowledge/nodes`

获取知识节点列表，支持按类型和关键词过滤。

**权限：** 需 JWT 认证

**查询参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `node_type` | string | 否 | — | 按节点类型过滤，可选值：`time` / `place` / `organization` / `topic` / `source` |
| `q` | string | 否 | — | 关键词搜索，匹配 name 和 description |

**排序规则：** 按 `node_type` 升序 + `name` 升序

**成功响应 (200)：**
```json
{
  "items": [
    {
      "id": 1,
      "name": "大学生活动中心大礼堂",
      "alias": null,
      "node_type": "place",
      "description": "活动地点",
      "source_url": null,
      "created_at": "2026-05-21T10:00:00",
      "updated_at": "2026-05-21T10:00:00",
      "embedding": null
    },
    {
      "id": 2,
      "name": "2026-05-10",
      "alias": null,
      "node_type": "time",
      "description": "活动日期",
      "source_url": null,
      "created_at": "2026-05-21T10:00:00",
      "updated_at": "2026-05-21T10:00:00",
      "embedding": null
    }
  ]
}
```

**错误码：**
- `401`：未提供 JWT

---

## `GET /api/knowledge/nodes/{id}`

获取单个知识节点详情，包含关联该节点的所有海报列表。

**权限：** 需 JWT 认证

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 知识节点 ID |

**成功响应 (200)：**
```json
{
  "item": {
    "id": 1,
    "name": "大学生活动中心大礼堂",
    "alias": null,
    "node_type": "place",
    "description": "活动地点",
    "source_url": null,
    "created_at": "2026-05-21T10:00:00",
    "updated_at": "2026-05-21T10:00:00",
    "embedding": null,
    "posters": [
      {
        "relation_type": "has_place",
        "matched_by": "rule",
        "poster": {
          "id": 1,
          "title": "AI 创新应用讲座",
          "status": "published"
        }
      }
    ]
  }
}
```

**`posters` 数组字段说明：**
| 字段 | 类型 | 说明 |
|------|------|------|
| `relation_type` | string | 关系类型，如 `has_place`、`has_time`、`has_org`、`has_topic`、`has_source` |
| `matched_by` | string | 匹配方式，当前固定为 `rule` |
| `poster` | object | 关联海报的 to_dict() 数据 |

**错误码：**
- `401`：未提供 JWT
- `404`：节点不存在

---

## `POST /api/knowledge/rebuild`

重建所有海报的知识节点关联与海报间关系。逐个处理每张海报，返回成功/失败计数。

**权限：** `admin`

**请求体：**
```json
{
  "status": "published",
  "source_type": "",
  "rebuild_embeddings": false
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `status` | string | 否 | `"published"` | 只重建此状态的海报，设为空字符串则重建所有 |
| `source_type` | string | 否 | — | 按来源类型过滤 |
| `rebuild_embeddings` | boolean | 否 | `false` | 是否同时重建向量嵌入（需启用 EMBEDDING_ENABLED） |

**处理流程：**
1. 查询符合条件的海报列表
2. 对每张海报：删除旧的 PosterNode 和 PosterLink，重新运行 `rebuild_poster_knowledge()`
3. 如果 `rebuild_embeddings=true` 且配置启用，触发异步嵌入重建任务
4. 创建审计日志

**成功响应 (200)：**
```json
{
  "total": 10,
  "succeeded": 9,
  "failed": 1,
  "errors": [
    { "id": 5, "error": "海报数据异常" }
  ],
  "embeddings": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**错误码：**
- `401`：未提供 JWT
- `403`：角色非 `admin`

---

## `GET /api/posters/{id}/related`

获取与指定海报相关的知识节点和关联海报。这是海报模块和知识库模块的交叉接口，提供"关联展示"的完整数据。

**权限：** 需 JWT 认证

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**响应结构说明：**
- `poster`：当前海报基本信息
- `knowledge_nodes`：直接关联的知识节点列表（一级关联）
- `related_posters`：与当前海报共享知识节点的其他海报（二级关联）
- `poster_links`：海报到海报的直接关系（同日期、同地点等）

**成功响应 (200)：**
```json
{
  "poster": {
    "id": 1,
    "title": "AI 创新应用讲座",
    "status": "published"
  },
  "knowledge_nodes": [
    {
      "id": 1,
      "poster_id": 1,
      "node_id": 2,
      "relation_type": "has_time",
      "matched_by": "rule",
      "node": {
        "id": 2,
        "name": "2026-05-10",
        "node_type": "time",
        "description": "活动日期"
      }
    },
    {
      "id": 2,
      "poster_id": 1,
      "node_id": 3,
      "relation_type": "has_place",
      "matched_by": "rule",
      "node": {
        "id": 3,
        "name": "大学生活动中心大礼堂",
        "node_type": "place",
        "description": "活动地点"
      }
    }
  ],
  "related_posters": [
    {
      "poster": {
        "id": 5,
        "title": "校园科技文化节开幕式",
        "status": "published"
      },
      "shared_node": {
        "id": 3,
        "name": "大学生活动中心大礼堂",
        "node_type": "place"
      },
      "relation_type": "has_place"
    }
  ],
  "poster_links": [
    {
      "id": 1,
      "direction": "outgoing",
      "link_type": "same_place",
      "created_by_rule": "location",
      "created_at": "2026-05-21T10:00:00",
      "related_poster": {
        "id": 5,
        "title": "校园科技文化节开幕式"
      }
    }
  ]
}
```

**响应字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `knowledge_nodes[].relation_type` | string | 海报→节点关系类型：`has_time` / `has_place` / `has_org` / `has_topic` / `has_source` |
| `knowledge_nodes[].matched_by` | string | 匹配方式，当前固定为 `rule` |
| `knowledge_nodes[].node` | object | 知识节点的完整 to_dict() 数据 |
| `related_posters[].shared_node` | object | 当前海报与关联海报共享的知识节点 |
| `related_posters[].relation_type` | string | 共享节点与关联海报的关系类型 |
| `poster_links[].direction` | string | `outgoing`（当前海报→关联海报）或 `incoming`（关联海报→当前海报） |
| `poster_links[].link_type` | string | 关系类型：`same_day` / `same_place` / `same_org` / `same_topic` |
| `poster_links[].created_by_rule` | string | 建边规则，如 `event_date` / `location` / `organizer` / `topic` |

**错误码：**
- `401`：未提供 JWT
- `404`：海报不存在
