# TODO List: 收尾与搜索对齐

> **阶段目标**：补齐剩余后端功能，更新文档。
> **更新日期**：2026-05-19

## 使用规范

1. 每完成一项，把 `[ ]` 改成 `[x]`
2. 在 `[x]` 后补充一句结果
3. 全部完成后，把本文件归档到 `docs/todos/`

---

## 搜索接口对齐

文档依据：7.4节要求 `GET /api/search/internal`（语义向量 + 全文检索）和 `GET /api/search/external`，当前内部搜索只有 LIKE。

- [x] 外部搜索统一：`GET /api/search/external` 路由指向 AI 搜索
- [x] 内部搜索增强：在全文 LIKE 基础上增加可选的向量语义检索（EMBEDDING_ENABLED 时启用）

## 文档更新

- [x] 更新 `docs/后端技术文档.md` — 环境变量表添加 Copilot Pro 说明
- [x] 更新 `docs/后端技术文档.md` — 补充 Model Manager / Dict Manager / Fallback Extractor 说明
- [x] 确认文档中的接口定义与当前代码一致（如 content_html 字段、dict API）

---

## 当前状态

```bash
cd /home/workspace/Campus-Activity-Information-Platform
git status --short --branch
```
