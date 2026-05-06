# 校园活动信息平台后端

这是第一版可运行后端骨架，目标是先把项目从“只有文档”推进到“本地能跑、服务器可部署、接口可联调”。

## 当前已落地

- Flask 应用工厂
- JWT 登录鉴权
- 海报基础接口
- SQLite 本地零配置启动
- PostgreSQL / Redis 部署入口
- Dockerfile 和 `docker-compose.yml`

## 目录结构

```text
backend
├─ app
│  ├─ api
│  ├─ services
│  ├─ utils
│  ├─ config.py
│  ├─ extensions.py
│  └─ models.py
├─ .env.example
├─ docker-compose.yml
├─ Dockerfile
├─ gunicorn.conf.py
├─ requirements.txt
└─ wsgi.py
```

## 本地启动

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python wsgi.py
```

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

```bash
cp .env.example .env
```

2. 把 `DATABASE_URL` 改成：

```env
DATABASE_URL=postgresql+psycopg://campus:campus123456@postgres:5432/campus_activity
```

3. 启动：

```bash
docker compose up -d --build
```

## 下一步建议

1. 接入 PostgreSQL 迁移工具和真实表结构演进。
2. 增加知识节点、关联关系、搜索接口。
3. 接入 Celery 任务队列和 Redis。
4. 增加外部抓取、审核流和日志审计。
