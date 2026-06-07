# 校园活动信息平台 — 后端

## 快速启动

```bash
cd backend
cp .env.example .env          # 编辑 .env 填入 API Key 等
python wsgi.py                # http://127.0.0.1:5000
```

默认管理员：`admin` / `admin123456`（在 `.env` 中配置）。

## 目录结构

```
backend/app/
├── api/           # 蓝图 (12 个) — 参数提取，调用 service，返回 JSON
├── services/      # 业务逻辑 (17 个) — 操作数据库，调用外部 API
├── models/        # 数据模型 — 按领域拆分 (user/poster/knowledge/...)
├── schemas/       # 响应 envelope 辅助函数
├── tasks/         # Celery 异步任务 (crawl / ai / index)
├── utils/         # 工具 (auth 装饰器 / 限流 / 搜索日志)
├── config.py      # 环境变量配置
├── extensions.py  # Flask 扩展初始化 (db, jwt, cors, redis)
└── __init__.py    # create_app() 工厂函数
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | Flask + Gunicorn |
| 数据库 | PostgreSQL + pgvector (生产) / SQLite (开发) |
| ORM | SQLAlchemy (Flask-SQLAlchemy) |
| 缓存/队列 | Redis |
| 异步任务 | Celery + Celery Beat |
| 认证 | JWT + 图形验证码 + 邮箱验证码 |
| AI | OpenAI 兼容 API (DeepSeek/OpenAI/Copilot Pro) |
| 搜索 | SearXNG 多引擎 + 搜狗微信 + 向量检索 (pgvector) |
| 部署 | Docker Compose + Nginx |

## 常用命令

```bash
# 开发
python wsgi.py                           # 启动开发服务器

# Docker
docker compose up -d                     # 完整环境
docker compose exec app python -m pytest tests/ -v  # 运行测试

# Flask CLI
flask --app wsgi init-db                 # 手动建表
flask --app wsgi seed-demo               # 填充演示数据
```

## 环境变量

见 `.env.example`。关键配置：

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 数据库连接 (默认 SQLite) |
| `REDIS_URL` | Redis 连接 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `LLM_API_KEY` | LLM API 密钥 |
| `EMBEDDING_ENABLED` | 是否开启向量检索 |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | 邮箱验证码 SMTP |
| `CORS_ORIGINS` | 跨域来源 (默认 `*`) |

## 开发规范

见项目根目录 [CLAUDE.md](../CLAUDE.md)。关键约定：

- API 层不直接操作 `db.session`，必须通过 service
- 禁止函数体内懒加载 import（Celery 任务例外）
- 新功能按 `models → services → schemas → api → tasks` 顺序开发
- 响应格式：列表 `{"items": [], "page": 1, "per_page": 10, "total": 30}`，单项 `{"data": {}}`

## 测试

```bash
docker compose exec app python -m pytest tests/ -v
```

- API 集成测试优先，每个端点至少一个 happy path + 一个 error case
- 外部依赖 (LLM API, MCP, HTTP) 需 mock
- 数据库用内存 SQLite，不 mock
