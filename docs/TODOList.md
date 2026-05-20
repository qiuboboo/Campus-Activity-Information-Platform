# TODOList: 技术文档与代码实现差距分析

> **阶段目标**：对照 `docs/后端技术文档.md` 找出已文档但未实现的功能，逐步补齐。
> **更新日期**：2026-05-20

## 使用规范

1. 每完成一项，把 `[ ]` 改成 `[x]`
2. 在 `[x]` 后补充一句结果
3. 全部完成后，把本文件归档到 `docs/todos/`

---

## 差距总览

对比技术文档与代码实现，主要发现：

- **文档中有但代码未实现**：向量 Embedding 流水线（占位符状态）
- **代码中有但文档未更新**：较多——AI/Dict/Knowledge/Export API、AuditLog 模型、质量评分/去重/审计系统、Poster 扩展字段
- **流程简化**：海报发布流程中"用户提交审核"步骤合并到管理员直接审核

---

## 一、向量 Embedding 流水线（文档有，代码未实现）

文档依据：
- 6.2 节：Poster 和 KnowledgeNode 均有 `embedding` vector 字段
- 5.5 节：内部搜索"优先采用语义向量检索"
- 7.4 节：返回 `search_mode` 标识 vector/fulltext
- 技术选型表：pgvector

当前状态：
- [x] `embedding` 列在模型中不存在 → 已添加 Text 类型 embedding 列到 Poster 和 KnowledgeNode
- [x] `tasks/index_tasks.py` 内有 `# TODO: call embedding API` 占位 → 已实现完整 embedding 生成逻辑
- [x] `search.py` 中有 vector 分支但只 `pass` → 已实现向量检索（余弦相似度）+ LIKE 兜底
- [x] 需要接入一个 Embedding API → 已通过 Copilot Pro 代理接入 `text-embedding-3-small`

## 二、Poster 工作流"提交审核"步骤

文档依据：5.2 节第 4-5 步 "用户确认后提交审核 → 管理员审核"

当前状态：
- [ ] 代码中只有 `draft` → (admin review) → `published`/`rejected`，缺少用户侧"提交审核"动作
- [ ] 是否补充 `pending_review` 状态和对应接口需确认

## 三、技术文档更新（代码已有，文档未同步）

### 6.2 节 — 数据库表结构
- [ ] `posters` 表：字段名 `content_raw` → `raw_text`（文档用名与代码不符）
- [ ] `posters` 表：补充 `duplicate_group_key`、`source_fingerprint`、`quality_score`、`quality_notes`、`tags`、`activity_type`、`last_crawled_at`
- [ ] `knowledge_nodes` 表：补充 `updated_at`
- [ ] `poster_links` 表：补充 `updated_at`
- [ ] `crawl_logs` 表：补充 `pages_found`、`pages_succeeded`、`pages_failed`、`duplicates_skipped`、`drafts_created`、`average_quality_score`
- [ ] `dict_entries` 表：`aliases` 字段格式说明（逗号分隔，非 JSON）
- [ ] 新增 `audit_logs` 表（已有模型但文档未收录）

### 7.x 节 — 接口设计
- [ ] 7.1 节：补充 `GET /api/auth/me`（当前用户信息）
- [ ] 7.2 节：补充 review-queue、bulk-review、duplicates、merge-source、rebuild-knowledge、ai-enrich 接口
- [ ] 7.5 节：补充 `GET /api/data-sources/{id}`、`PUT /api/data-sources/{id}`、`GET /api/data-sources/{id}/logs`
- [ ] 7.6 新增：知识节点接口 `GET /api/knowledge/nodes`、`GET /api/knowledge/nodes/{id}`、`POST /api/knowledge/rebuild`
- [ ] 7.7 新增：AI 接口 `/api/ai/*`（status、extract、enrich、search、mcp）
- [ ] 7.8 新增：Dict 受控词表接口 `/api/dict/*`
- [ ] 7.9 新增：导出与演示接口 `/api/export/*`、`/api/demo/summary`
- [ ] 7.10 新增：系统接口 `/api/health`、`/api/tasks/{id}`、`/api/audit-logs`

### 5.x 节 — 模块说明
- [ ] 补充质量评分系统说明（`quality_service.py`）
- [ ] 补充去重系统说明（`dedup_service.py`）
- [ ] 补充审计日志系统说明（`audit_service.py`）

---

## 优先级建议

1. **P0** — 向量 Embedding 流水线（文档核心承诺功能，答辩重点）
2. **P1** — 文档 6.2/7.x 同步更新（代码已有但文档落后，影响团队理解）
3. **P2** — Poster 工作流"提交审核"步骤（用户体验改进，非阻塞）
4. **P2** — 文档 5.x 新增模块说明（质量/去重/审计）
