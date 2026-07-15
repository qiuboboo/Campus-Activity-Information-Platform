# 逸仙活动云前端

校园活动信息平台的 Vue 3 前端。公开端、发布者工作区和管理端均使用统一的前端领域模型：`Activity`、`/activities`、`/activity/:id`；后端实体命名不会进入页面或路由。

## 本地启动

需要 Node.js 18+。

```bash
npm install

# 终端 1：启动 Mock
node mock/index.js

# 终端 2：启动前端
npm run dev
```

访问 `http://127.0.0.1:3000`。Mock 账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin123456` |
| 发布者 | `zhangsan` | `123456` |

登录和注册包含图形验证码；Mock 会生成可见验证码图片。

## 质量命令

```bash
npm run build
npm run test:unit
npm run test:e2e
npm run verify
```

`verify` 会顺序执行构建、单元测试与端到端测试。Windows 若受执行策略影响，可使用 `npm.cmd run verify`。

## 环境与后端联调

复制 `.env.example` 为 `.env.local`，按部署环境设置 `VITE_API_BASE_URL`。默认 `/api` 由 Vite 开发代理转发到 `http://127.0.0.1:5000`。

前端对外保持 `/activities` 和 `Activity` 格式；生产网关或 API 适配层负责与后端资源进行转换。请勿在页面、路由或组件中改用后端实体名。已冻结接口、待确认接口和联调边界见：[前后端契约矩阵](docs/frontend-plan/BACKEND_CONTRACT_MATRIX.md) 与 [后端联调清单](docs/frontend-plan/BACKEND_INTEGRATION_CHECKLIST.md)。

## 已覆盖流程

- 访客搜索、筛选和活动详情
- 图形验证码登录、邮箱验证码注册、登录回跳与权限路由
- 报名幂等、收藏、日历加入/移除、ICS 导出、知识关联与订阅
- 发布者创建草稿、提交审核；管理员审核批准
- 数据源、审计日志和受限导出

## 文档

- [全站建设与交付状态](docs/frontend-plan/2026-07-13-full-site-build-checklist.md)
- [前后端契约矩阵](docs/frontend-plan/BACKEND_CONTRACT_MATRIX.md)
- [本地测试指南](docs/前端本地测试指南.md)
- [页面设计文档](docs/frontend-design)
