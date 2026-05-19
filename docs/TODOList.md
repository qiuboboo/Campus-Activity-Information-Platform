# TODO List: 后端增强

> **阶段目标**：补齐文档中已规划但未实现的功能，增强后端健壮性。
> **更新日期**：2026-05-19

## 使用规范

1. 每完成一项，把 `[ ]` 改成 `[x]`
2. 在 `[x]` 后补充一句结果
3. 全部完成后，把本文件归档到 `docs/todos/`

---

## Model Manager（模型管理模块）

文档依据：config.py 已有 `list_llm_profiles()`，ai_service.py 的 `_llm_chat()` 只读 default profile，没有按 name 分发的能力。

- [ ] 创建 `services/model_manager.py`
  - 封装 `list_llm_profiles()` 的读取逻辑
  - 实现 `get_llm_client(profile_name="default")` 返回对应模型的 key/base_url/model
  - 实现多模型切换：API 层传入 `model` 参数选择 profile
- [ ] 改造 `ai_service.py` 的 `_llm_chat()` 支持 `profile` 参数
  - 不传则走默认模型
  - 传入 profile name 则走对应模型配置
- [ ] 更新 API 层：`POST /ai/extract` 支持 `model` 可选字段

## 非 AI 兜底提取（Fallback Extractor）

文档依据：5.7节明确要求"所有 AI 功能都有对应的非 AI 兜底实现"，当前 `extract_from_text()` 在 LLM 不可用时只返回空 dict。

- [ ] 创建 `services/fallback_extractor.py`
  - 正则提取标题（取第一段非空行，限 80 字）
  - 正则提取时间（匹配 `\d{4}年\d{1,2}月\d{1,2}日`、`\d{1,2}月\d{1,2}日`、ISO 格式等）
  - 正则提取地点（匹配"在...举行/举办/召开"等句式 + 地点字典匹配）
  - 正则提取主办方（匹配"由...主办/承办/组织"等句式）
  - 简单摘要（取 raw_text 前 120 字）
- [ ] 改造 `extract_from_text()`：LLM 失败时自动降级到 fallback extractor
- [ ] 正确返回结构化字段（即使不如 LLM 准确，也要有值）

## 字典标准化模块

文档依据：5.3节要求维护"小型受控词表和别名表，用于统一名称"，当前 `_topic_from_poster()` 的关键词硬编码在函数里。

- [ ] 创建 `services/dict_manager.py`
  - 地点字典 API：标准名称 ↔ 别名映射
  - 组织字典 API：部门/学院标准名称 ↔ 别名
  - 主题标签表 API：同义词映射（如"大活礼堂"→"大学生活动中心大礼堂"）
- [ ] 接入知识节点生成：`_node_specs_for_poster()` 中的 location/organizer 走字典标准化
- [ ] 利用 KnowledgeNode 模型的 `alias` 字段（当前存在但从未被 populate）
- [ ] 提供管理 API：`GET/POST /api/dict/places`、`GET/POST /api/dict/orgs`

## 海报 HTML 生成

文档依据：5.2节"生成简约 HTML 海报"，Poster 模型文档中有 `content_html` 字段但实际 model 中没有该字段。

- [ ] Poster 模型添加 `content_html` 字段
- [ ] 实现 HTML 海报生成函数（基于标题/时间/地点/主办方等字段，生成简约 HTML）
- [ ] 创建海报时自动生成 content_html
- [ ] 迁移：补全已有海报的 content_html

## Celery 异步任务补齐

文档依据：9.1节要求三个队列（crawl / ai / index），当前只有 crawl 任务。

- [ ] 创建 `tasks/ai_tasks.py` — AI 异步任务（ai 队列）
  - `ai_extract_task(text)` — 异步调用 LLM 提取
  - `ai_enrich_task(poster_id)` — 异步调用 LLM 增强
- [ ] 创建 `tasks/index_tasks.py` — 向量索引任务（index 队列）
  - `build_poster_embedding(poster_id)` — 生成海报向量
  - `build_node_embedding(node_id)` — 生成知识节点向量
- [ ] 更新 `celery_app.py` 配置三个队列路由

## 搜索接口对齐

文档依据：7.4节要求 `GET /api/search/internal`（语义向量 + 全文检索）和 `GET /api/search/external`，当前内部搜索只有 LIKE，外部搜索在 `POST /ai/search` 路径不一致。

- [ ] 内部搜索增强：在全文 LIKE 基础上增加可选的向量语义检索（EMBEDDING_ENABLED 时启用）
- [ ] 外部搜索统一：`GET /api/search/external` 路由指向 AI 搜索（或保持现状，更新文档）

---

## 当前状态

```bash
cd /home/workspace/Campus-Activity-Information-Platform
git status --short --branch
```
