# 前后端契约矩阵

本表以当前前端的 `Activity` 页面模型为基准。后端将持久化实体称作 `poster`，但该命名不会进入用户界面或路由；前端通过接口层处理差异。

| 前端能力 | 已采用的后端资源 | 状态 | 说明 |
| --- | --- | --- | --- |
| 登录、注册 | `GET /auth/captcha`、`POST /auth/login`、`POST /auth/register`、`POST /auth/send-code`、`GET /auth/me` | 已接入 | 验证码图片以 Blob 显示，令牌从 `X-Captcha-Token` 读取；`/auth/me` 同时兼容 `{ user }` 包装响应。 |
| 订阅、通知 | `/subscriptions`、`/notifications` | 已接入 | 节点和关键词都可订阅；“全部已读”在前端逐条调用 `PUT /notifications/{id}/read`，不假定批量接口存在。 |
| 个人日历 | `/calendar/events`、`/posters/{id}/ics` | 已接入 | 支持加入、移除和 ICS 导出；页面仍使用“活动”作为展示词。 |
| 关联展示 | `/posters/{id}/related`、`/knowledge/nodes` | 已接入 | 详情页在核心详情加载成功后异步加载关联信息；关联失败不会阻断阅读。 |
| 管理审核、数据源、审计、导出 | `/posters/*/review`、`/data-sources`、`/audit-logs`、`/demo/summary`、`/export/posters.json` | 已接入 | 保持现有管理端信息架构，不将抓取或审核业务判断复制到浏览器。 |
| 附件上传 | 当前 Mock：`POST /uploads`、`DELETE /uploads/{id}` | 待接口冻结 | 使用 `multipart/form-data` 的 `file` 字段；前端附件对象为 `id/name/url/mime_type/size`。Mock 仅验证文件流程，真实后端需确认存储、鉴权和下载策略。 |
| 公共活动列表、详情、创建编辑 | 当前 Mock：`/activities`；后端文档：`/posters` | 待后端确认适配 | 前端路由固定为 `/activities` 和 `/activity/:id`；需要后端确认列表权限与“我的发布”查询参数后，再在 API 适配层统一切换资源路径。 |
| 报名与独立收藏 | 当前 Mock：`/activities/{id}/register`、`/favorite` | 待接口冻结 | 后端总文档未定义报名或独立收藏资源；日历收藏已接入，报名不能假定真实后端可用。 |
| 资料更新、忘记密码 | 当前 Mock：`PATCH /auth/me`、`POST /auth/forgot-password` | 待接口冻结 | 后端总文档只冻结了认证、验证码和当前用户读取接口。 |

## 联调原则

- 页面和路由继续使用 `Activity` 作为前端领域模型，避免把后端表名扩散到组件。
- 对已冻结资源，页面只使用文档中存在的 HTTP 方法和路径；Mock 提供同一路径的最小成功、未授权和失败状态。
- 对“待接口冻结”项，Mock 仅用于前端流程和测试，不能作为真实后端能力的证明。
