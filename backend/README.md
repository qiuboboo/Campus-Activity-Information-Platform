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

<<<<<<< Updated upstream
## 常用命令
=======
默认地址：`http://127.0.0.1:5000`

默认管理员账号在 `.env` 中配置：

- 用户名：`admin`
- 密码：`admin123456`

## 初始化数据库

默认开发环境开启 `AUTO_CREATE_TABLES=true`，首次启动会自动建表并创建默认管理员。

也可以手动执行：

```powershell
flask --app wsgi init-db
flask --app wsgi seed-demo
```

## 数据库迁移（生产环境）

项目使用 Flask-Migrate/Alembic 管理表结构版本。新建数据库执行：

```powershell
flask --app wsgi db upgrade
```

已有 SQLite 或 PostgreSQL 数据库在首次切换前应先备份；若它已由本项目
的 `AUTO_CREATE_TABLES=true` 初始化并已处于当前模型版本，执行下面命令只
写入迁移版本标记，不会建表、删表或修改业务数据：

```powershell
flask --app wsgi db stamp head
```

之后每次模型变更均生成并提交迁移：

```powershell
flask --app wsgi db migrate -m "描述本次结构变更"
flask --app wsgi db upgrade
```

## 已实现接口

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/posters`
- `POST /api/posters`
- `GET /api/posters/{id}`
- `PUT /api/posters/{id}`
- `POST /api/posters/{id}/review`

## 登录示例

```json
POST /api/auth/login
{
  "username": "admin",
  "password": "admin123456"
}
```

## Docker 部署

1. 复制环境变量文件：
>>>>>>> Stashed changes

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

<<<<<<< Updated upstream
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
=======
3. 启动（Compose 会在 Gunicorn 前自动执行 `flask db upgrade`）：
>>>>>>> Stashed changes

```bash
docker compose exec app python -m pytest tests/ -v
```
<<<<<<< Updated upstream

- API 集成测试优先，每个端点至少一个 happy path + 一个 error case
- 外部依赖 (LLM API, MCP, HTTP) 需 mock
- 数据库用内存 SQLite，不 mock
=======
>>>>>>> Stashed changes
