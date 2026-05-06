# Server Backend Deployment TODO List

本文是服务器后端初步部署的勾选式执行清单，适合交给执行者逐项完成。执行时默认：

- 系统级操作使用 `root`
- 开发、运行、验证使用 `workspace`
- 项目目录为 `/home/workspace/校园活动平台`

如遇失败，不要跳过，先记录报错，再继续处理。

## 0. 开始前

- [ ] 确认当前服务器系统为 Ubuntu 22.04
- [ ] 确认 `workspace` 用户存在
- [ ] 确认 Docker 已安装并可执行
- [ ] 确认 Python 3 / pip3 / git 可用
- [ ] 确认项目代码已经位于服务器，或可以从 GitHub 拉取

## 1. 检查基础环境

- [ ] 执行 `whoami`，确认当前用户身份
- [ ] 执行 `python3 --version`
- [ ] 执行 `pip3 --version`
- [ ] 执行 `git --version`
- [ ] 执行 `docker --version`
- [ ] 执行 `docker ps`
- [ ] 记录检查结果

## 2. 准备项目目录

- [ ] 检查 `/home/workspace/校园活动平台` 是否存在
- [ ] 如果项目在 `/root` 下，复制到 `/home/workspace/`
- [ ] 执行 `sudo chown -R workspace:workspace /home/workspace/校园活动平台`
- [ ] 确认项目目录下包含 `backend/`、`deploy/`、`docs/`

## 3. 切换到 workspace

- [ ] 执行 `su - workspace`
- [ ] 执行 `whoami`，确认是 `workspace`
- [ ] 执行 `echo $HOME`，确认是 `/home/workspace`
- [ ] 记录当前工作目录与用户状态

## 4. 检查 workspace 开发环境

- [ ] 执行 `node -v`
- [ ] 执行 `npm -v`
- [ ] 如果执行者需要在服务器使用 Claude Code，确认 Node 版本为 `18+`
- [ ] 确认当前用户不依赖 `/root/.nvm/...`

## 5. 准备 Python 虚拟环境

- [ ] 进入 `/home/workspace/校园活动平台/backend`
- [ ] 执行 `python3 -m venv .venv`
- [ ] 执行 `source .venv/bin/activate`
- [ ] 执行 `pip install --upgrade pip`
- [ ] 执行 `pip install -r requirements.txt`
- [ ] 记录依赖安装是否成功

## 6. 准备环境变量

- [ ] 执行 `cp .env.example .env`
- [ ] 检查 `.env` 是否存在
- [ ] 确认 `DATABASE_URL=sqlite:///app.db`
- [ ] 确认 `AUTO_CREATE_TABLES=true`
- [ ] 将 `JWT_SECRET_KEY` 改为非默认值
- [ ] 记录当前 `.env` 使用的是 SQLite 模式

## 7. 用 Python 方式启动后端

- [ ] 在 `backend` 目录执行 `source .venv/bin/activate`
- [ ] 执行 `python wsgi.py`
- [ ] 确认服务监听在 `0.0.0.0:5000`
- [ ] 若启动失败，记录完整报错

## 8. 验证健康检查接口

- [ ] 另开终端执行 `curl http://127.0.0.1:5000/api/health`
- [ ] 确认返回 `status: ok` 或等价成功结果
- [ ] 记录健康检查结果

## 9. 验证登录接口

- [ ] 执行登录请求：
- [ ] `curl -X POST http://127.0.0.1:5000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123456"}'`
- [ ] 确认能返回 token
- [ ] 记录登录接口结果

## 10. 检查 Docker 运行路径

- [ ] 确认 `backend/docker-compose.yml` 存在
- [ ] 检查当前 `.env` 是否仍是 SQLite
- [ ] 决定 Docker 阶段是否切换到 PostgreSQL 模式
- [ ] 如果要跑完整 Docker 组合，修改 `DATABASE_URL` 为 PostgreSQL 容器地址

## 11. 用 Docker Compose 启动后端

- [ ] 在 `backend` 目录执行 `docker compose up -d --build`
- [ ] 执行 `docker compose ps`
- [ ] 执行 `docker compose logs --tail=100 api`
- [ ] 记录 `api`、`postgres`、`redis` 是否启动成功

## 12. 再次验证接口

- [ ] 执行 `curl http://127.0.0.1:5000/api/health`
- [ ] 确认 Docker 方式下接口仍然可访问
- [ ] 必要时再次验证登录接口

## 13. 可选的外网访问检查

- [ ] 确认服务器安全组/防火墙是否允许 `22`
- [ ] 如需外网直连调试，确认是否开放 `5000`
- [ ] 如不需要外网调试，记录“暂不开放 5000”

## 14. 结果记录

- [ ] 记录项目部署目录
- [ ] 记录 Python 直跑是否成功
- [ ] 记录 Docker Compose 是否成功
- [ ] 记录当前数据库模式是 SQLite 还是 PostgreSQL
- [ ] 记录健康检查接口结果
- [ ] 记录登录接口结果
- [ ] 记录下一步建议

## 15. 下一步建议

- [ ] 评估是否接入 Nginx
- [ ] 评估是否接入域名与 HTTPS
- [ ] 评估是否切换为 PostgreSQL 正式模式
- [ ] 评估是否需要 Redis 真正启用
- [ ] 评估是否开始前后端联调
