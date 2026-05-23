# Activity Detail 设计文档

说明：本文件为 `ActivityDetail` 页面设计规范（页面目标、组件拆分、数据合同、交互流程、响应式与无障碍要求、Mock 要求与验收标准）。

## 页面目标
- 以清晰、可访问的方式展示单个活动的全部关键信息，支持报名、分享、收藏等受权限控制的交互；便于前后端联调与测试。

## 页面布局（高层）
- 顶部区：返回按钮、面包屑、标题、动作按钮（报名、分享、收藏、举报）
- 正文区（主列）：活动摘要、正文（支持 HTML/Markdown 渲染）、图片/附件列表
- 侧栏（右列，可折叠）：活动元信息（时间、地点、组织者、类型、状态、统计）、相关活动、快速链接

## 组件拆分
- `ActivityDetail.vue`（页面容器，负责数据加载、错误/加载状态、SEO 标题）
- `ActivityHeader.vue`（标题、面包屑、主要动作按钮）
- `ActivityBody.vue`（摘要 + 正文渲染 + 图片/附件画廊）
- `ActivityMeta.vue`（时间/地点/组织者/类型/状态/统计 + 报名控件）
- `ActivityRelated.vue`（相关活动列表）

组件职责简述与 Props
- `ActivityDetail`
  - Props: 无（路由 param: `id`）
  - 责任：从 `GET /api/activities/:id` 拉取数据；将 `activity` 传给子组件；处理 `?redirect=` / `?source=` 查询；错误与 404 展示。
- `ActivityHeader`
  - Props: `title: string`, `status: string`, `onBack()`
- `ActivityBody`
  - Props: `summary`, `raw_text`, `attachments[]`；在安全沙箱中渲染 `raw_text`（优先 sanitize）
- `ActivityMeta`
  - Props: `event_time`, `location`, `organizer`, `activity_type`, `meta`；包含 `register()` 方法回调

## 数据合同（API）
- GET /api/activities/:id
  - 200 示例：
  ```json
  {
    "id": 1,
    "title": "示例活动",
    "summary": "简短摘要",
    "raw_text": "<p>活动正文</p>",
    "event_time": "2026-06-15T09:00:00",
    "location": "广州校区",
    "organizer": "学生会",
    "status": "published",
    "activity_type": "讲座",
    "attachments": [{"url":"/media/1.png","name":"海报"}],
    "tags": ["学术","公开"],
    "meta": {"views":123, "registrations":45},
    "created_at": "2026-05-20T10:00:00"
  }
  ```
  - 404：{ "message": "activity not found" }

- POST /api/activities/:id/register
  - 请求：身份需登录（Token），返回 `{ success: true, registrations: <number> }` 或错误码

## 交互流程要点
- 页面加载：显示骨架屏 -> 请求成功后渲染 -> 失败显示 404 或错误提示
- 报名流程：
  1. 未登录：跳转 `/login?redirect=<current full url>`
  2. 已登录：调用 `POST /api/activities/:id/register`，成功后刷新 `meta.registrations` 并显示成功提示
- 分享/收藏：UI 触发本地交互（若后端支持，调用相应 API）；尚未实现项显示“内容未实现！”占位
- 返回行为：优先使用 `redirect` query（若存在），否则 `history.back()`，否则跳回首页

## 响应式与无障碍（a11y）
- 移动端：主列置顶，侧栏折叠为下拉或 accordion；图片采用懒加载与手势滑动
- 键盘导航：所有动作按钮可 tab 聚焦并可回车触发；主要图片与附件有可访问替代文本
- 语义化：使用 `header`, `main`, `aside`, `time` 等语义标签；为时间、地点、组织者使用 `aria-label`
- 对比度与文本大小：满足 WCAG AA 基线；操作按钮大小 ≥44px 触控目标

## Mock 要求与测试数据
- Mock endpoints（已在 `frontend/mock/routes/activity.js` 增补）：
  - `GET /api/activities/:id`（示例返回包含 attachments/tags/meta）
  - `POST /api/activities/:id/register`（模拟报名，增加 registrations）
  - `GET /api/search/internal` 与 `GET /api/search/external`（用于相关/搜索联调）
- 本地示例凭据（见 `2026-05-24-plan.md`）：`admin/admin123456`，`zhangsan/123456`

## 验收标准（验收用例）
1. 给定活动 ID，页面能展示 `title`、`event_time`、`location`、`organizer`、`activity_type`、`status`。
2. 正文（`raw_text`）安全渲染，图片/附件可点击下载或查看。
3. 报名按钮：未登录时跳转登录并保存 `redirect`，登录后调用报名接口并更新 `registrations`。
4. 对无效 ID 返回 404 页面，含友好提示与返回链接。
5. 页面在窄屏与宽屏下布局合理，按钮可触控/键盘操作。

## 测试要点
- 单元测试（Vitest）：
  - Mock `GET /api/activities/:id`，断言 `title` 与 `event_time` 渲染
  - 模拟点击报名：未登录时断言跳转至 `/login?redirect=...`；已登录时断言调用 `POST /api/activities/:id/register`
- 集成/手工：在 dev 模式下使用 mock server 验证搜索/相关活动联动

## 估时
- 撰写文档：1h（已完成）
- 前端实现（样式+交互+单测）：2.5h
- 联调与无障碍检查：1h

---
文件结束。
