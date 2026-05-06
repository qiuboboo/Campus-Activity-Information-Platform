# Server Backend Deployment TODO List

本文是服务器后端初步部署的勾选式执行清单，适合交给执行者逐项完成。执行时默认：

- 系统级操作使用 `root`
- 开发、运行、验证使用 `workspace`
- 项目目录为 `/home/workspace/Campus-Activity-Information-Platform`

如遇失败，不要跳过，先记录报错，再继续处理。

## 0. 开始前

- [x] 确认当前服务器系统为 Ubuntu 22.04
- [x] 确认 `workspace` 用户存在
- [x] 确认 Docker 已安装并可执行
- [x] 确认 Python 3 / pip3 / git 可用
- [x] 确认项目代码已经位于服务器，或可以从 GitHub 拉取

## 1. 检查基础环境

- [x] 执行 `whoami`，确认当前用户身份
- [x] 执行 `python3 --version`
- [x] 执行 `pip3 --version`
- [x] 执行 `git --version`
- [x] 执行 `docker --version`
- [x] 执行 `docker ps`
- [x] 记录检查结果

## 2. 准备项目目录

- [x] 检查 `/home/workspace/Campus-Activity-Information-Platform` 是否存在
- [x] 如果项目在 `/root` 下，复制到 `/home/workspace/`
- [x] 执行 `sudo chown -R workspace:workspace /home/workspace/Campus-Activity-Information-Platform`
- [x] 确认项目目录下包含 `backend/`、`deploy/`、`docs/`

## 3. 切换到 workspace

- [x] 执行 `su - workspace`
- [x] 执行 `whoami`，确认是 `workspace`
- [x] 执行 `echo $HOME`，确认是 `/home/workspace`
- [x] 记录当前工作目录与用户状态

## 4. 检查 workspace 开发环境

- [x] 执行 `node -v`
- [x] 执行 `npm -v`
- [x] 如果执行者需要在服务器使用 Claude Code，确认 Node 版本为 `18+`
- [x] 确认当前用户不依赖 `/root/.nvm/...`

## 5. 准备 Python 虚拟环境

- [x] 进入 `/home/workspace/Campus-Activity-Information-Platform/backend`
- [x] 执行 `python3 -m venv .venv`
- [x] 执行 `source .venv/bin/activate`
- [x] 执行 `pip install --upgrade pip`
- [x] 执行 `pip install -r requirements.txt`
- [x] 记录依赖安装是否成功 — **成功，所有 35 个包已安装**

## 6. 准备环境变量

- [x] 执行 `cp .env.example .env`
- [x] 检查 `.env` 是否存在
- [x] 确认 `DATABASE_URL=sqlite:///app.db` — **Python 直跑使用 SQLite，Docker 使用 PostgreSQL**
- [x] 确认 `AUTO_CREATE_TABLES=true`
- [x] 将 `JWT_SECRET_KEY` 改为非默认值
- [x] 记录当前 `.env` 使用的是 SQLite 模式（Python 直跑） / PostgreSQL 模式（Docker Compose）

## 7. 用 Python 方式启动后端

- [x] 在 `backend` 目录执行 `source .venv/bin/activate`
- [x] 执行 `python wsgi.py`
- [x] 确认服务监听在 `0.0.0.0:5000`
- [x] 若启动失败，记录完整报错 — **首次启动成功**

## 8. 验证健康检查接口

- [x] 另开终端执行 `curl http://127.0.0.1:5000/api/health`
- [x] 确认返回 `status: ok` 或等价成功结果
- [x] 记录健康检查结果 — **`{"status":"ok","database":"ok","service":"campus-activity-backend"}`**

## 9. 验证登录接口

- [x] 执行登录请求：
- [x] `curl -X POST http://127.0.0.1:5000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123456"}'`
- [x] 确认能返回 token
- [x] 记录登录接口结果 — **成功返回 JWT token 和用户信息**

## 10. 检查 Docker 运行路径

- [x] 确认 `backend/docker-compose.yml` 存在
- [x] 检查当前 `.env` 是否仍是 SQLite — **Docker 已切换为 PostgreSQL**
- [x] 决定 Docker 阶段是否切换到 PostgreSQL 模式 — **已切换**
- [x] 如果要跑完整 Docker 组合，修改 `DATABASE_URL` 为 PostgreSQL 容器地址 — **已修改为 `postgresql+psycopg://campus:campus123456@postgres:5432/campus_activity`**

## 11. 用 Docker Compose 启动后端

- [x] 在 `backend` 目录执行 `docker compose up -d --build`
- [x] 执行 `docker compose ps`
- [x] 执行 `docker compose logs --tail=100 api`
- [x] 记录 `api`、`postgres`、`redis` 是否启动成功 — **全部启动成功**

> 注意：需将 `workspace` 用户加入 `docker` 组 (`usermod -aG docker workspace`)，否则需使用 `newgrp docker` 切换。
>
> Dockerfile 已添加清华 PyPI 镜像 (`-i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple`) 解决容器内 pip 超时问题。
>
> bootstrap.py 已添加 `IntegrityError` 处理，解决多 Gunicorn Worker 并发创建 admin 用户的竞态条件。

## 12. 再次验证接口

- [x] 执行 `curl http://127.0.0.1:5000/api/health`
- [x] 确认 Docker 方式下接口仍然可访问
- [x] 必要时再次验证登录接口 — **均正常**

## 13. 可选的外网访问检查

- [x] 确认服务器安全组/防火墙是否允许 `22` — **SSH(22) 已开放**
- [x] 如需外网直连调试，确认是否开放 `5000` — **端口 5000 已对外暴露**
- [x] 如不需要外网调试，记录”暂不开放 5000” — **注意：5432(PostgreSQL) 和 6379(Redis) 也对外暴露，建议通过 Nginx 反向代理并限制端口**

## 14. 结果记录

- [x] 记录项目部署目录 — **`/home/workspace/Campus-Activity-Information-Platform`**
- [x] 记录 Python 直跑是否成功 — **成功**
- [x] 记录 Docker Compose 是否成功 — **成功（3 个容器: api + postgres + redis）**
- [x] 记录当前数据库模式是 SQLite 还是 PostgreSQL — **Python 直跑使用 SQLite，Docker 使用 PostgreSQL**
- [x] 记录健康检查接口结果 — **`{"status":"ok","database":"ok","service":"campus-activity-backend"}`**
- [x] 记录登录接口结果 — **返回 JWT token，admin 用户登录成功**
- [x] 记录下一步建议 — **见第 15 节**

## 15. 下一步建议

- [x] 评估是否接入 Nginx — **建议接入 Nginx 反向代理 API 并限制 5432/6379 端口外网访问**
- [x] 评估是否接入域名与 HTTPS — **如对外提供服务则建议**
- [x] 评估是否切换为 PostgreSQL 正式模式 — **Docker 已在用 PostgreSQL，Python 直跑仍用 SQLite**
- [x] 评估是否需要 Redis 真正启用 — **Redis 已部署，Celery 任务待启用**
- [x] 评估是否开始前后端联调 — **后端就绪，可开始联调**
