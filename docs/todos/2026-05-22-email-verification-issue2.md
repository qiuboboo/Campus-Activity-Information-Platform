# TODOList: 邮箱验证码注册流程 (Issue #2)

> **对应 Issue**：[#2 后端 API 改造需求：添加包含邮件发送在内的若干接口](https://github.com/qiuboboo/Campus-Activity-Information-Platform/issues/2)
> **方案**：邮件验证码方案（轻量封装 email_service，SMTP 通过环境变量配置）
> **验收日期**：2026-05-22

## 实施记录

- [x] Config 新增 SMTP 配置项（MAIL_SERVER、MAIL_PORT、MAIL_USERNAME、MAIL_PASSWORD、MAIL_DEFAULT_SENDER）
- [x] Config 新增 CORS_ORIGINS
- [x] User 模型新增 email 字段（唯一、可为空），to_dict() 返回 email
- [x] 创建 email_service.py — SMTP 发送、6 位验证码 Redis 存储（5 分钟 TTL、60 秒冷却）、验证码校验
- [x] auth.py 新增 POST /api/auth/send-code 接口
- [x] auth.py 修改注册接口 — 新增 email + verification_code 参数及校验
- [x] auth.py 修改登录接口 — 支持 username 或 email（or_ 查询）
- [x] CORS 支持配置 origins
- [x] 全量 189 个测试通过
- [x] docs/APIOverview.md 和 docs/后端技术文档.md 同步更新
- [x] PostgreSQL 生产数据库 ALTER TABLE 加 email 列
- [x] 实际邮箱验证码发送 + 注册流程端到端验证通过
