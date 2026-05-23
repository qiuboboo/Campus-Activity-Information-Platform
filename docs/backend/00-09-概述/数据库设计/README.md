# 数据库设计

## 1. 核心表概览

| 表名 | 用途 |
| --- | --- |
| `users` | 存储用户与角色 |
| `posters` | 存储活动海报及结构化信息 |
| `knowledge_nodes` | 存储知识节点 |
| `poster_node` | 海报与知识节点的多对多关联 |
| `poster_links` | 海报与海报之间的关联 |
| `data_sources` | 外部数据源配置 |
| `crawl_logs` | 抓取任务日志 |
| `audit_logs` | 审计日志 |
| `dict_entries` | 受控词表（地点/组织/主题的别名标准化） |

## 2. 主要表结构说明

### `users`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `username` | varchar | 用户名 |
| `email` | varchar | 邮箱（唯一，可为空） |
| `password_hash` | varchar | 密码哈希 |
| `role` | varchar | 角色 |
| `created_at` | timestamp | 创建时间 |

### `posters`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `title` | varchar | 活动标题 |
| `summary` | text | 活动简介 |
| `raw_text` | text | 原始文本 |
| `content_html` | text | 生成的海报 HTML |
| `event_time` | timestamp | 活动时间 |
| `location` | varchar | 活动地点 |
| `organizer` | varchar | 主办方 |
| `status` | varchar | draft/published/rejected |
| `source_type` | varchar | manual/crawl/ai |
| `source_url` | text | 来源链接 |
| `embedding` | text | 向量嵌入（JSON 数组，1536 维 float） |
| `review_comment` | text | 审核意见 |
| `created_by` | bigint | 创建人 |
| `duplicate_group_key` | varchar(64) | 去重分组标识 |
| `source_fingerprint` | varchar(64) | 来源指纹（内容哈希） |
| `quality_score` | int | 质量评分（0-100） |
| `quality_notes` | text | 质量评分说明 |
| `tags` | text | 标签（逗号分隔） |
| `activity_type` | varchar(50) | 活动类型（如讲座/晚会/竞赛） |
| `last_crawled_at` | timestamp | 最后抓取时间 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

### `knowledge_nodes`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `name` | varchar | 节点名称 |
| `alias` | text | 别名列表 |
| `node_type` | varchar | 节点类型 |
| `description` | text | 描述 |
| `source_url` | text | 来源链接 |
| `embedding` | text | 向量嵌入（JSON 数组） |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

### `poster_node`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `poster_id` | bigint | 海报 ID |
| `node_id` | bigint | 知识节点 ID |
| `relation_type` | varchar | 关系类型 |
| `matched_by` | varchar | 匹配来源：rule/ai/manual |

### `poster_links`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `from_poster_id` | bigint | 起始海报 ID |
| `to_poster_id` | bigint | 目标海报 ID |
| `link_type` | varchar | 关联类型，如 same_time/same_place/same_org/same_topic |
| `created_by_rule` | varchar | 建链规则来源 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

### `data_sources`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `name` | varchar | 数据源名称 |
| `base_url` | text | 数据源入口 |
| `list_selector` | varchar | 列表选择器 |
| `content_selector` | varchar | 正文选择器 |
| `enabled` | boolean | 是否启用 |
| `crawl_mode` | varchar | basic/mcp/weixin |
| `source_level` | varchar | official/internal/external |
| `owner` | varchar | 负责人 |
| `notes` | text | 备注 |
| `allowed_domains` | text | 爬虫域名白名单，逗号分隔 |
| `request_interval` | int | 请求间隔（秒），默认 2 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |
| `last_success_at` | timestamp | 最后成功时间 |
| `last_failure_at` | timestamp | 最后失败时间 |
| `last_error_message` | text | 最后错误信息 |

### `crawl_logs`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `data_source_id` | bigint | 数据源 ID |
| `status` | varchar | running/success/failure |
| `message` | text | 执行信息 |
| `started_at` | timestamp | 开始时间 |
| `finished_at` | timestamp | 结束时间 |
| `pages_found` | int | 找到的页面数 |
| `pages_succeeded` | int | 成功抓取页面数 |
| `pages_failed` | int | 失败页面数 |
| `duplicates_skipped` | int | 跳过重复数 |
| `drafts_created` | int | 生成的草稿数 |
| `average_quality_score` | float | 平均质量评分 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

### `audit_logs`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `actor_id` | bigint | 操作人 ID（外键 → users.id） |
| `action` | varchar | 操作类型，如 review/rebuild/merge |
| `target_type` | varchar | 操作对象类型 |
| `target_id` | int | 操作对象 ID |
| `summary` | text | 操作摘要 |
| `metadata_json` | text | 额外元数据（JSON） |
| `created_at` | timestamp | 创建时间 |

### `dict_entries`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `category` | varchar | 词条类别：place/org/topic |
| `standard_name` | varchar | 标准名称 |
| `aliases` | text | 别名列表（逗号分隔） |
| `description` | text | 描述说明 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

### `subscriptions`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `user_id` | bigint | 用户 ID（外键 → users.id） |
| `node_id` | bigint | 知识节点 ID（外键 → knowledge_nodes.id，可为空） |
| `keyword` | varchar | 关键词订阅（可为空，与 node_id 二选一） |
| `notify_method` | varchar | 通知方式：platform / email / webhook |
| `created_at` | timestamp | 创建时间 |

### `notifications`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `user_id` | bigint | 接收用户 ID |
| `poster_id` | bigint | 关联海报 ID |
| `title` | varchar | 通知标题 |
| `body` | text | 通知内容 |
| `is_read` | boolean | 是否已读 |
| `created_at` | timestamp | 创建时间 |

### `user_calendar_events`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `user_id` | bigint | 用户 ID |
| `poster_id` | bigint | 海报 ID |
| `added_at` | timestamp | 添加时间 |

## 3. 关系说明

- 一个用户可以创建多个海报
- 一个海报可以关联多个知识节点
- 一个知识节点也可以被多个海报关联
- 海报之间可以通过 `poster_links` 建立多种横向联系
- 一个数据源可以对应多条抓取日志
- 一个用户可以订阅多个知识节点；一个知识节点可被多个用户订阅
- 一个用户可以收藏多个海报到个人日历；一个海报可被多个用户收藏
