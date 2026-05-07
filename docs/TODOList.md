# TODO List: Activity Governance and Admin Workflow

本文是下一轮较长后端任务清单。目标是把当前“能抓取、能生成草稿、能审核发布、能建知识图谱”的后端，推进为更完整的活动治理后台：抓取草稿进入审核队列、支持重复识别、支持批量审核、记录审计日志、评估草稿质量、支持知识图谱重建，并提供课程演示导出接口。

默认约定：

- 项目操作使用 `workspace`
- 项目目录为 `/home/workspace/Campus-Activity-Information-Platform`
- 后端通过 Docker Compose 运行
- Celery worker 已可用，但本轮不新增 Celery Beat
- 本轮不处理 HTTPS、域名、证书、OpenClaw、前端页面
- 本轮优先实现非 AI、规则化、可解释的治理能力
- 本轮接口应优先服务后续管理后台前端
- 完成后更新 `docs/DeploymentRecord.md`

## 0. 拉取与检查

- [x] 以 `workspace` 用户进入项目目录
- [x] 执行 `cd /home/workspace/Campus-Activity-Information-Platform`
- [x] 执行 `git status --short --branch`
- [x] 确认没有未提交本地改动
- [x] 执行 `git pull --ff-only`
- [x] 记录起始 commit
- [x] 执行 `python -m compileall backend`

## 1. 扩展活动治理字段

- [x] 在 `Poster` 中增加 `duplicate_group_key`
- [x] 在 `Poster` 中增加 `source_fingerprint`
- [x] 在 `Poster` 中增加 `quality_score`
- [x] 在 `Poster` 中增加 `quality_notes`
- [x] 在 `Poster` 中增加 `last_crawled_at`
- [x] 保持旧数据兼容
- [x] 更新 `Poster.to_dict()`

## 2. 扩展数据源治理字段

- [x] 在 `DataSource` 中增加 `source_level`
- [x] 在 `DataSource` 中增加 `owner`
- [x] 在 `DataSource` 中增加 `notes`
- [x] 在 `DataSource` 中增加 `last_success_at`
- [x] 在 `DataSource` 中增加 `last_failure_at`
- [x] 在 `DataSource` 中增加 `last_error_message`
- [x] 更新 `DataSource.to_dict()`
- [x] 更新创建和更新数据源接口，允许写入这些字段

## 3. 新增审计日志模型

- [x] 新增 `AuditLog`
- [x] 字段包含 `actor_id`
- [x] 字段包含 `action`
- [x] 字段包含 `target_type`
- [x] 字段包含 `target_id`
- [x] 字段包含 `summary`
- [x] 字段包含 `metadata_json`
- [x] 字段包含 `created_at`
- [x] 实现 `AuditLog.to_dict()`
- [x] 新增 `backend/app/services/audit_service.py`
- [x] 实现 `create_audit_log()`

## 4. 实现重复识别服务

- [x] 新增 `backend/app/services/dedup_service.py`
- [x] 根据标题标准化生成 title key
- [x] 根据日期生成 date key
- [x] 根据地点标准化生成 location key
- [x] 根据来源链接生成 source key
- [x] 生成 `source_fingerprint`
- [x] 生成 `duplicate_group_key`
- [x] 抓取创建草稿前先检测相同 `source_url`
- [x] 再检测相同 `source_fingerprint`
- [x] 对完全重复内容跳过创建
- [x] 对疑似重复内容创建草稿但标记 `duplicate_group_key`
- [x] 抓取结果返回重复数量

## 5. 实现草稿质量评分

- [x] 新增 `backend/app/services/quality_service.py`
- [x] 标题为空或过短扣分
- [x] 摘要为空扣分
- [x] 无活动时间扣分
- [x] 无地点扣分
- [x] 无来源链接扣分
- [x] 正文过短扣分
- [x] 疑似重复扣分
- [x] 官方来源加分
- [x] 生成 `quality_score`
- [x] 生成 `quality_notes`
- [x] 抓取生成草稿时自动评分
- [x] 抓取日志记录本次新增草稿平均质量

## 6. 增强抓取日志

- [x] 为 `CrawlLog` 增加 `duplicates_skipped`
- [x] 为 `CrawlLog` 增加 `drafts_created`
- [x] 为 `CrawlLog` 增加 `average_quality_score`
- [x] 更新 `CrawlLog.to_dict()`
- [x] 更新 `finish_crawl_log()`
- [x] 更新同步抓取结果结构
- [x] 更新 Celery 抓取任务返回结构
- [x] 确保旧日志可正常序列化

## 7. 实现审核队列 API

- [x] 新增或扩展 `GET /api/posters/review-queue`
- [x] 支持按 `status` 过滤
- [x] 支持按 `source_type` 过滤
- [x] 支持按 `data_source_id` 过滤
- [x] 支持按 `duplicate_group_key` 过滤
- [x] 支持按 `quality_score` 排序
- [x] 支持分页
- [x] 返回每条草稿的质量评分和重复信息
- [x] 接口要求 admin 权限

## 8. 实现批量审核 API

- [x] 新增 `POST /api/posters/bulk-review`
- [x] 支持批量 `approve`
- [x] 支持批量 `reject`
- [x] 支持批量添加 `review_comment`
- [x] 单条失败不影响其他条目
- [x] 返回成功列表
- [x] 返回失败列表
- [x] 每条审核动作写入 `AuditLog`
- [x] 审核通过后沿用现有知识节点与关系生成逻辑

## 9. 增强单条审核审计

- [x] 保留现有单条审核接口兼容
- [x] 审核通过后自动补齐知识节点
- [x] 审核驳回后记录驳回原因
- [x] 审核操作写入 `AuditLog`
- [x] 返回审核后的关联摘要

## 10. 实现重复与来源合并 API

- [x] 新增 `GET /api/posters/{id}/duplicates`
- [x] 返回同 `source_fingerprint` 的海报
- [x] 返回同 `duplicate_group_key` 的海报
- [x] 新增 `POST /api/posters/{id}/merge-source`
- [x] 合并时保留主海报
- [x] 合并时记录被合并来源链接
- [x] 合并时写入审计日志
- [x] 合并后可选择重新生成知识图谱

## 11. 实现知识图谱维护 API

- [x] 新增 `POST /api/posters/{id}/rebuild-knowledge`
- [x] 清理该海报旧的 `PosterNode`
- [x] 清理该海报相关旧的 `PosterLink`
- [x] 重新生成知识节点
- [x] 重新生成关联边
- [x] 写入审计日志
- [x] 新增 `POST /api/knowledge/rebuild`
- [x] 支持按状态过滤
- [x] 支持按 `source_type` 过滤
- [x] 默认只处理 `published` 海报
- [x] 返回处理数量、成功数量、失败数量
- [x] 如任务较重，使用 Celery 异步执行

## 12. 实现审计日志 API

- [x] 新增 `backend/app/api/audit_logs.py`
- [x] 注册 audit logs 蓝图
- [x] 实现 `GET /api/audit-logs`
- [x] 支持按 `actor_id` 过滤
- [x] 支持按 `action` 过滤
- [x] 支持按 `target_type` 过滤
- [x] 支持分页
- [x] 仅 admin 可访问

## 13. 实现课程演示导出 API

- [x] 新增 `GET /api/export/posters.json`
- [x] 新增 `GET /api/export/knowledge.json`
- [x] 新增 `GET /api/export/crawl-report.json`
- [x] 新增 `GET /api/demo/summary`
- [x] 导出中不包含密码哈希和敏感配置
- [x] `demo/summary` 返回海报总数
- [x] `demo/summary` 返回已发布数量
- [x] `demo/summary` 返回抓取草稿数量
- [x] `demo/summary` 返回知识节点数量
- [x] `demo/summary` 返回海报关系数量
- [x] `demo/summary` 返回数据源数量
- [x] `demo/summary` 返回最近一次抓取摘要
- [x] 仅 admin 可访问导出接口

## 14. 文档更新

- [x] 更新 `docs/APIExamples.md`
- [x] 添加审核队列示例
- [x] 添加批量审核示例
- [x] 添加重复检测示例
- [x] 添加来源合并示例
- [x] 添加重建知识图谱示例
- [x] 添加审计日志查询示例
- [x] 添加导出接口示例
- [x] 如示例较长，新增 `docs/AdminWorkflowExamples.md`

## 15. 本地或服务器语法验证

- [x] 执行 `python -m compileall backend`
- [x] 确认 Flask app 可以启动
- [x] 确认 Celery worker 可以启动
- [x] 确认 `/api/health` 正常
- [x] 确认登录接口正常

## 16. 服务器 Docker 验证

- [x] 进入 `backend` 目录
- [x] 执行 `docker compose down`
- [x] 执行 `docker compose up -d --build`
- [x] 确认 `api`、`worker`、`postgres`、`redis` 都运行
- [x] 登录 admin
- [x] 触发一次异步抓取
- [x] 查询审核队列
- [x] 批量审核 2 条草稿
- [x] 验证知识图谱生成
- [x] 验证重复检测
- [x] 验证审计日志
- [x] 验证导出接口
- [x] 记录 Docker 内存占用

## 17. 更新记录

- [x] 更新 `docs/DeploymentRecord.md`
- [x] 写明新增模型字段
- [x] 写明新增 API
- [x] 写明重复检测策略
- [x] 写明质量评分策略
- [x] 写明审核队列和批量审核验证结果
- [x] 写明审计日志验证结果
- [x] 写明导出接口验证结果
- [x] 明确记录本轮未处理 HTTPS、域名、OpenClaw、前端页面

## 18. 提交与推送

- [x] 执行 `git status --short`
- [x] 确认只包含本轮代码与文档变更
- [x] 执行 `git add backend docs`
- [x] 执行 `git commit -m "Implement activity governance workflow"`
- [x] 执行 `git push`

## 可拆分建议

- [x] 如果一次性太大，第一轮先做审核队列、批量审核、审计日志
- [x] 第二轮做重复检测、来源合并、质量评分
- [x] 第三轮做知识图谱重建、导出接口、演示报告
