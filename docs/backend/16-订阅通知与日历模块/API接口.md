# 订阅通知与日历 API

---

## 订阅接口

### `POST /api/subscriptions`

创建订阅，支持按知识节点（`node_id`）或关键词（`keyword`）订阅，两者至少提供一个但不能同时提供。

**权限：** 需 JWT 认证（任意角色）

**请求体（按知识节点订阅）：**
```json
{
  "node_id": 7,
  "notify_method": "platform"
}
```

**请求体（按关键词订阅）：**
```json
{
  "keyword": "讲座",
  "notify_method": "platform"
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `node_id` | int | 二选一 | 知识节点 ID，与 `keyword` 二选一 |
| `keyword` | string | 二选一 | 订阅关键词，用于匹配海报标题、类型、标签、地点、主办方，与 `node_id` 二选一 |
| `notify_method` | string | 否 | 通知方式，默认 `"platform"`，当前仅支持平台内通知 |

**成功响应 (201)——新建：**
```json
{
  "item": {
    "id": 1,
    "user_id": 42,
    "node_id": 7,
    "keyword": null,
    "notify_method": "platform",
    "node": {
      "id": 7,
      "name": "大礼堂",
      "node_type": "place",
      ...
    },
    "created_at": "2026-05-24T10:00:00"
  }
}
```

**成功响应 (200)——已存在重复订阅，直接返回现有记录：**
```json
{
  "item": {
    "id": 1,
    "user_id": 42,
    "node_id": 7,
    "keyword": null,
    "notify_method": "platform",
    "node": { ... },
    "created_at": "2026-05-24T10:00:00"
  }
}
```

**错误码：**
- `400`：既未提供 `node_id` 也未提供 `keyword` — `{"message": "node_id or keyword is required"}`
- `400`：同时提供了 `node_id` 和 `keyword` — `{"message": "provide either node_id or keyword, not both"}`
- `401`：未认证

---

### `GET /api/subscriptions`

查看当前用户的订阅列表。

**权限：** 需 JWT 认证（任意角色）

**查询参数：** 无

**成功响应 (200)：**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 42,
      "node_id": 7,
      "keyword": null,
      "notify_method": "platform",
      "node": {
        "id": 7,
        "name": "大礼堂",
        "node_type": "place"
      },
      "created_at": "2026-05-24T10:00:00"
    },
    {
      "id": 2,
      "user_id": 42,
      "node_id": null,
      "keyword": "讲座",
      "notify_method": "platform",
      "node": null,
      "created_at": "2026-05-24T11:00:00"
    }
  ],
  "total": 2
}
```

**错误码：**
- `401`：未认证

---

### `DELETE /api/subscriptions/{id}`

取消订阅。

**权限：** 需 JWT 认证（任意角色，仅能删除自己的订阅）

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 订阅记录 ID |

**请求体：** 无

**成功响应 (200)：**
```json
{
  "message": "subscription cancelled"
}
```

**错误码：**
- `403`：尝试删除其他用户的订阅 — `{"message": "permission denied"}`
- `404`：订阅不存在
- `401`：未认证

---

## 通知接口

### `GET /api/notifications`

查看当前用户的通知列表。

**权限：** 需 JWT 认证（任意角色）

**查询参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `is_read` | string | 否 | — | 过滤已读/未读，取值 `"true"` 或 `"false"`。不传则返回全部 |

**成功响应 (200)：**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 42,
      "poster_id": 100,
      "title": "新活动发布：校园科技文化节",
      "body": "您订阅的内容有新活动：校园科技文化节",
      "is_read": false,
      "created_at": "2026-05-24T12:00:00",
      "poster": {
        "id": 100,
        "title": "校园科技文化节"
      }
    }
  ],
  "total": 1,
  "unread_count": 1
}
```

**错误码：**
- `401`：未认证

---

### `PUT /api/notifications/{id}/read`

标记单条通知为已读。

**权限：** 需 JWT 认证（任意角色，仅能标记自己的通知）

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 通知 ID |

**请求体：** 无

**成功响应 (200)：**
```json
{
  "item": {
    "id": 1,
    "user_id": 42,
    "poster_id": 100,
    "title": "新活动发布：校园科技文化节",
    "body": "您订阅的内容有新活动：校园科技文化节",
    "is_read": true,
    "created_at": "2026-05-24T12:00:00",
    "poster": {
      "id": 100,
      "title": "校园科技文化节"
    }
  }
}
```

**错误码：**
- `403`：尝试操作其他用户的通知 — `{"message": "permission denied"}`
- `404`：通知不存在
- `401`：未认证

---

### `PUT /api/notifications/read-all`

标记当前用户所有未读通知为已读。

**权限：** 需 JWT 认证（任意角色）

**请求体：** 无

**成功响应 (200)：**
```json
{
  "message": "marked 3 notifications as read",
  "updated": 3
}
```

**错误码：**
- `401`：未认证

---

## 日历接口

### `GET /api/posters/{id}/ics`

下载单张海报的 .ics 日历文件。公开接口，无需认证。

**权限：** 公开（无需 JWT）

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 海报 ID |

**查询参数：** 无

**成功响应 (200)：** 返回 `text/calendar` 格式的 ICS 文件内容，符合 RFC 5545 标准。

```
Content-Type: text/calendar; charset=utf-8
Content-Disposition: attachment; filename="activity-14.ics"

BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Campus Activity Platform//CN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:poster-14@campus-activity-platform
DTSTAMP:20260524T120000Z
DTSTART:20260510T190000Z
DTEND:20260510T210000Z
SUMMARY:校园科技文化节
DESCRIPTION:一年一度的科技文化节...
LOCATION:大礼堂
END:VEVENT
END:VCALENDAR
```

**字段说明：**
- `DTSTART`/`DTEND`：取自海报的 `event_time`，持续时间默认为 2 小时；如无 `event_time` 则使用 `created_at`，持续 1 天

**错误码：**
- `404`：海报不存在或状态不是 `published` — `{"error": "poster not published"}`

---

### `POST /api/calendar/events`

将已发布海报添加到"我的日历"。

**权限：** 需 JWT 认证（任意角色）

**请求体：**
```json
{
  "poster_id": 14
}
```

**成功响应 (201)——新建：**
```json
{
  "item": {
    "id": 5,
    "user_id": 42,
    "poster_id": 14,
    "added_at": "2026-05-24T12:00:00",
    "poster": {
      "id": 14,
      "title": "校园科技文化节",
      "event_time": "2026-05-10T19:00:00",
      ...
    }
  }
}
```

**成功响应 (200)——已存在（幂等）：**
```json
{
  "item": { ... }
}
```

**错误码：**
- `400`：缺少 `poster_id` — `{"message": "poster_id is required"}`
- `404`：海报不存在或未发布 — `{"error": "poster not found or not published"}`
- `401`：未认证

---

### `GET /api/calendar/events`

获取当前用户的日历活动列表，按活动时间升序排列。

**权限：** 需 JWT 认证（任意角色）

**查询参数：** 无

**成功响应 (200)：**
```json
{
  "items": [
    {
      "id": 5,
      "user_id": 42,
      "poster_id": 14,
      "added_at": "2026-05-24T12:00:00",
      "poster": {
        "id": 14,
        "title": "校园科技文化节",
        "event_time": "2026-05-10T19:00:00",
        "location": "大礼堂",
        ...
      }
    }
  ],
  "total": 1
}
```

**错误码：**
- `401`：未认证

---

### `DELETE /api/calendar/events/{poster_id}`

从"我的日历"中移除一个活动。

**权限：** 需 JWT 认证（任意角色）

**路径参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `poster_id` | int | 要移除的海报 ID |

**请求体：** 无

**成功响应 (200)：**
```json
{
  "message": "event removed from calendar"
}
```

**错误码：**
- `404`：该活动不在用户的日历中 — `{"error": "event not found in your calendar"}`
- `401`：未认证
