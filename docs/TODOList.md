# TODO List: Celery Async Crawl Queue

本文是下一轮后端功能开发清单。目标是把当前同步执行的 `POST /api/data-sources/{id}/crawl` 改造成 `Celery + Redis` 异步任务队列。服务器已完成 swap 与内存稳定化，但本轮仍要保持保守并发，避免再次造成内存压力。

默认约定：

- 项目操作使用 `workspace`
- 项目目录为 `/home/workspace/Campus-Activity-Information-Platform`
- 后端通过 Docker Compose 运行
- 本轮不处理 HTTPS、域名、证书、OpenClaw、前端页面
- 本轮不实现 Celery Beat 和定时任务
- Worker 初始并发固定为 `1`
- 继续使用现有 Redis 容器作为 broker
- 继续复用现有同步抓取函数，避免大改业务逻辑
- 完成后更新 `docs/DeploymentRecord.md`

## 0. 拉取与检查

- [ ] 以 `workspace` 用户进入项目目录
- [ ] 执行 `cd /home/workspace/Campus-Activity-Information-Platform`
- [ ] 执行 `git status --short --branch`
- [ ] 确认没有未提交本地改动
- [ ] 执行 `git pull --ff-only`
- [ ] 记录起始 commit
- [ ] 执行 `python -m compileall backend`

## 1. 确认内存与 Redis 基线

- [ ] 执行 `free -h`
- [ ] 执行 `swapon --show`
- [ ] 执行 `docker stats --no-stream`
- [ ] 执行 `docker compose -f backend/docker-compose.yml ps`
- [ ] 确认 swap 已启用
- [ ] 确认 Redis 容器运行正常
- [ ] 记录 Celery 改造前容器内存占用

## 2. 新增 Celery 应用初始化

- [ ] 新增 `backend/app/celery_app.py`
- [ ] 从 Flask `Config.REDIS_URL` 读取 broker
- [ ] 从 Flask `Config.REDIS_URL` 读取 result backend
- [ ] 确保 Celery task 内可以访问 Flask app context
- [ ] 避免 worker import 时重复触发数据库建表竞态
- [ ] 确保 Celery app 能加载后续 `app.tasks` 模块

## 3. 新增抓取任务模块

- [ ] 新增 `backend/app/tasks/__init__.py`
- [ ] 新增 `backend/app/tasks/crawl_tasks.py`
- [ ] 实现 `crawl_data_source_task(data_source_id, user_id)`
- [ ] task 内调用现有 `crawl_data_source(data_source_id, user_id)`
- [ ] 捕获异常并返回结构化错误
- [ ] 返回结果至少包含 `success`
- [ ] 返回结果至少包含 `posters_created`
- [ ] 返回结果至少包含 `pages_found`
- [ ] 返回结果至少包含 `pages_succeeded`
- [ ] 返回结果至少包含 `pages_failed`

## 4. 改造抓取 API

- [ ] 修改 `backend/app/api/data_sources.py`
- [ ] `POST /api/data-sources/{id}/crawl` 默认提交 Celery 任务
- [ ] 默认返回 `202 Accepted`
- [ ] 返回 `task_id`
- [ ] 返回 `status_url`，例如 `/api/tasks/{task_id}`
- [ ] 保留同步调试模式
- [ ] 请求体传 `{"sync": true}` 时仍同步执行现有抓取逻辑
- [ ] 数据源不存在时仍返回 `404`
- [ ] 非 admin 仍不能触发抓取

## 5. 新增任务状态 API

- [ ] 新增 `backend/app/api/tasks.py`
- [ ] 在 `backend/app/__init__.py` 注册 tasks 蓝图
- [ ] 实现 `GET /api/tasks/{task_id}`
- [ ] 返回 `task_id`
- [ ] 返回 `state`
- [ ] 返回 `result`
- [ ] 返回 `error`
- [ ] 接口需要 JWT 登录
- [ ] 对未知或过期 task 返回清晰状态

## 6. Docker Compose 增加 worker

- [ ] 修改 `backend/docker-compose.yml`
- [ ] 新增 `worker` 服务
- [ ] worker 使用与 `api` 相同 build
- [ ] worker 使用同一个 `.env`
- [ ] worker 依赖 `postgres` 和 `redis`
- [ ] worker 不暴露端口
- [ ] worker 设置 `restart: unless-stopped`
- [ ] worker command 使用 `celery -A app.celery_app.celery worker --loglevel=INFO --concurrency=1`
- [ ] 保持 API、PostgreSQL、Redis 现有启动方式

## 7. 文档与接口示例

- [ ] 更新 `docs/APIExamples.md`
- [ ] 添加异步触发抓取示例
- [ ] 添加查询任务状态示例
- [ ] 添加同步调试模式示例
- [ ] 写明 worker 并发为 `1`
- [ ] 写明本轮不启用 Celery Beat

## 8. 本地或服务器语法验证

- [ ] 执行 `python -m compileall backend`
- [ ] 确认 Celery 模块可以 import
- [ ] 确认 Flask app 可以启动
- [ ] 确认 `/api/health` 不受影响
- [ ] 确认登录接口不受影响

## 9. 服务器 Docker 验证

- [ ] 进入 `backend` 目录
- [ ] 执行 `docker compose down`
- [ ] 执行 `docker compose up -d --build`
- [ ] 执行 `docker compose ps`
- [ ] 确认存在 `api`
- [ ] 确认存在 `worker`
- [ ] 确认存在 `postgres`
- [ ] 确认存在 `redis`
- [ ] 执行 `docker compose logs --tail=100 worker`
- [ ] 确认 worker 正常连接 Redis
- [ ] 执行 `curl http://127.0.0.1/api/health`
- [ ] 登录并记录 JWT token

## 10. 异步抓取验收

- [ ] 选择已有 `中山大学计算机学院学术活动` 数据源，或重新创建该数据源
- [ ] 调用 `POST /api/data-sources/{id}/crawl`
- [ ] 确认返回 `202`
- [ ] 确认返回 `task_id`
- [ ] 使用 `GET /api/tasks/{task_id}` 查询状态
- [ ] 确认任务最终为 `SUCCESS`
- [ ] 确认任务结果包含页面统计
- [ ] 确认抓取完成后生成或跳过重复海报草稿
- [ ] 确认 `crawl_logs` 写入成功或失败日志
- [ ] 调用 `POST /api/data-sources/{id}/crawl` 并传 `{"sync": true}`
- [ ] 确认同步调试模式仍可运行

## 11. 内存观察

- [ ] 执行 `docker stats --no-stream`
- [ ] 触发一次异步真实站点抓取
- [ ] 每隔 30 秒执行一次 `docker stats --no-stream`，至少 3 次
- [ ] 执行 `free -h`
- [ ] 记录 API、worker、PostgreSQL、Redis 内存占用
- [ ] 确认 worker 并发为 `1`
- [ ] 如果 worker 内存过高，不提高并发，并记录下一步优化方向

## 12. 更新记录

- [ ] 更新 `docs/DeploymentRecord.md`
- [ ] 写明新增 Celery app 与 task 模块
- [ ] 写明 Docker Compose worker 配置
- [ ] 写明异步抓取接口验证结果
- [ ] 写明任务状态接口验证结果
- [ ] 写明同步调试模式验证结果
- [ ] 写明 worker 内存观察结果
- [ ] 明确记录本轮未处理 HTTPS、域名、OpenClaw、Celery Beat、定时任务

## 13. 提交与推送

- [ ] 执行 `git status --short`
- [ ] 确认只包含本轮代码与文档变更
- [ ] 执行 `git add backend docs`
- [ ] 执行 `git commit -m "Implement Celery async crawl queue"`
- [ ] 执行 `git push`

## 下一轮建议

- [ ] 如果异步抓取稳定，下一轮实现 Celery Beat 定时抓取
- [ ] 如果 worker 内存偏高，下一轮优化抓取分页、响应大小和任务分批
- [ ] 如果任务状态体验不足，下一轮补充任务历史表或任务审计表
