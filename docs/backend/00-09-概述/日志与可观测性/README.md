# 日志与可观测性

## 1. 请求访问日志

每次 HTTP 请求自动记录：
- 时间、方法、路径、状态码、响应耗时（ms）
- 每条请求自动分配请求 ID（`request_id`），透传至审计日志

实现在 `backend/app/__init__.py` 的 `_register_request_logging()` 和 `_register_request_id()` 中。

## 2. 审计日志（`audit_logs` 表）

业务操作记录，通过 `create_audit_log()` 写入：
- 用户登录
- 海报创建、编辑、提交审核、审核通过/驳回
- 抓取任务执行结果
- 知识图谱重建
- LLM / MCP 调用
- 数据源变更

审计日志包含：操作人、操作类型、目标对象、摘要、元数据（JSON）。

## 3. 搜索可观测性日志（`search_logger.py`）

每次搜索调用输出一行结构化 JSON 日志，用于排错、性能监控和用量分析。

**实现位置：** `backend/app/utils/search_logger.py`

**日志字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `endpoint` | string | `internal` 或 `external` |
| `query_masked` | string | 脱敏后的搜索关键词（中文保留首尾各一字，英文首尾各一字符） |
| `latency_ms` | float | 搜索耗时（毫秒） |
| `hit_count` | int | 结果总数 |
| `result_types` | object | 按类型统计的结果数，如 `{"poster": 5, "knowledge_node": 3}` 或 `{"google": 2, "baidu": 1}` |
| `search_mode` | string | `fulltext` / `vector` / `multi` / `none` |
| `sort` | string\|null | 排序字段（仅 internal） |
| `order` | string\|null | 排序方向（仅 internal） |
| `error` | string\|null | 错误描述（仅 external，正常时为 null） |
| `request_id` | string | HTTP 请求 ID，可关联到请求访问日志 |
| `user_id` | int\|null | 发起请求的用户 ID |
| `timestamp` | string | ISO 8601 时间戳 |

**脱敏规则（`mask_query()`）：**
- 空字符串 → `""`
- 中文 ≤ 2 字 → 原样保留；中文 > 2 字 → `首字***尾字`
- 非中文 ≤ 3 字符 → 原样保留；非中文 > 3 字符 → `首***尾`

**示例日志行：**
```json
{"endpoint":"internal","query_masked":"AI***座","latency_ms":12.34,"hit_count":5,"result_types":{"poster":3,"knowledge_node":2},"search_mode":"fulltext","sort":"relevance","order":"desc","error":null,"request_id":"a1b2c3d4","user_id":42,"timestamp":"2026-05-24T12:00:00.123456Z"}
```

## 4. 健康检查

`GET /api/health` 返回数据库与 Redis 连接状态，可用于外部监控探针。
