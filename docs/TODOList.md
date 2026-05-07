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

- [x] 以 `workspace` 用户进入项目目录
- [x] 执行 `cd /home/workspace/Campus-Activity-Information-Platform`
- [x] 执行 `git status --short --branch`
- [x] 确认没有未提交本地改动
- [x] 执行 `git pull --ff-only`
- [x] 记录起始 commit
- [x] 执行 `python -m compileall backend`

## 1. 确认内存与 Redis 基线

- [x] 执行 `free -h`
- [x] 执行 `swapon --show`
- [x] 执行 `docker stats --no-stream`
- [x] 执行 `docker compose -f backend/docker-compose.yml ps`
- [x] 确认 swap 已启用
- [x] 确认 Redis 容器运行正常
- [x] 记录 Celery 改造前容器内存占用

## 2. 新增 Celery 应用初始化

- [x] 新增 `backend/app/celery_app.py`
- [x] 从 Flask `Config.REDIS_URL` 读取 broker
- [x] 从 Flask `Config.REDIS_URL` 读取 result backend
- [x] 确保 Celery task 内可以访问 Flask app context
- [x] 避免 worker import 时重复触发数据库建表竞态
- [x] 确保 Celery app 能加载后续 `app.tasks` 模块

## 3. 新增抓取任务模块

- [x] 新增 `backend/app/tasks/__init__.py`
- [x] 新增 `backend/app/tasks/crawl_tasks.py`
- [x] 实现 `crawl_data_source_task(data_source_id, user_id)`
- [x] task 内调用现有 `crawl_data_source(data_source_id, user_id)`
- [x] 捕获异常并返回结构化错误
- [x] 返回结果至少包含 `success`
- [x] 返回结果至少包含 `posters_created`
- [x] 返回结果至少包含 `pages_found`
- [x] 返回结果至少包含 `pages_succeeded`
- [x] 返回结果至少包含 `pages_failed`

## 4. 改造抓取 API

- [x] 修改 `backend/app/api/data_sources.py`
- [x] `POST /api/data-sources/{id}/crawl` 默认提交 Celery 任务
- [x] 默认返回 `202 Accepted`
- [x] 返回 `task_id`
- [x] 返回 `status_url`，例如 `/api/tasks/{task_id}`
- [x] 保留同步调试模式
- [x] 请求体传 `{"sync": true}` 时仍同步执行现有抓取逻辑
- [x] 数据源不存在时仍返回 `404`
- [x] 非 admin 仍不能触发抓取

## 5. 新增任务状态 API

- [x] 新增 `backend/app/api/tasks.py`
- [x] 在 `backend/app/__init__.py` 注册 tasks 蓝图
- [x] 实现 `GET /api/tasks/{task_id}`
- [x] 返回 `task_id`
- [x] 返回 `state`
- [x] 返回 `result`
- [x] 返回 `error`
- [x] 接口需要 JWT 登录
- [x] 对未知或过期 task 返回清晰状态

## 6. Docker Compose 增加 worker

- [x] 修改 `backend/docker-compose.yml`
- [x] 新增 `worker` 服务
- [x] worker 使用与 `api` 相同 build
- [x] worker 使用同一个 `.env`
- [x] worker 依赖 `postgres` 和 `redis`
- [x] worker 不暴露端口
- [x] worker 设置 `restart: unless-stopped`
- [x] worker command 使用 `celery -A app.celery_app.celery worker --loglevel=INFO --concurrency=1`
- [x] 保持 API、PostgreSQL、Redis 现有启动方式

## 7. 文档与接口示例

- [x] 更新 `docs/APIExamples.md`
- [x] 添加异步触发抓取示例
- [x] 添加查询任务状态示例
- [x] 添加同步调试模式示例
- [x] 写明 worker 并发为 `1`
- [x] 写明本轮不启用 Celery Beat

## 8. 本地或服务器语法验证

- [x] 执行 `python -m compileall backend`
- [x] 确认 Celery 模块可以 import
- [x] 确认 Flask app 可以启动
- [x] 确认 `/api/health` 不受影响
- [x] 确认登录接口不受影响

## 9. 服务器 Docker 验证

- [x] 进入 `backend` 目录
- [x] 执行 `docker compose down`
- [x] 执行 `docker compose up -d --build`
- [x] 执行 `docker compose ps`
- [x] 确认存在 `api`
- [x] 确认存在 `worker`
- [x] 确认存在 `postgres`
- [x] 确认存在 `redis`
- [x] 执行 `docker compose logs --tail=100 worker`
- [x] 确认 worker 正常连接 Redis
- [x] 执行 `curl http://127.0.0.1/api/health`
- [x] 登录并记录 JWT token

## 10. 异步抓取验收

- [x] 选择已有 `中山大学计算机学院学术活动` 数据源，或重新创建该数据源
- [x] 调用 `POST /api/data-sources/{id}/crawl`
- [x] 确认返回 `202`
- [x] 确认返回 `task_id`
- [x] 使用 `GET /api/tasks/{task_id}` 查询状态
- [x] 确认任务最终为 `SUCCESS`
- [x] 确认任务结果包含页面统计
- [x] 确认抓取完成后生成或跳过重复海报草稿
- [x] 确认 `crawl_logs` 写入成功或失败日志
- [x] 调用 `POST /api/data-sources/{id}/crawl` 并传 `{"sync": true}`
- [x] 确认同步调试模式仍可运行

## 11. 内存观察

- [x] 执行 `docker stats --no-stream`
- [x] 触发一次异步真实站点抓取
- [x] 每隔 30 秒执行一次 `docker stats --no-stream`，至少 3 次
- [x] 执行 `free -h`
- [x] 记录 API、worker、PostgreSQL、Redis 内存占用
- [x] 确认 worker 并发为 `1`
- [x] 如果 worker 内存过高，不提高并发，并记录下一步优化方向

## 12. 更新记录

- [x] 更新 `docs/DeploymentRecord.md`
- [x] 写明新增 Celery app 与 task 模块
- [x] 写明 Docker Compose worker 配置
- [x] 写明异步抓取接口验证结果
- [x] 写明任务状态接口验证结果
- [x] 写明同步调试模式验证结果
- [x] 写明 worker 内存观察结果
- [x] 明确记录本轮未处理 HTTPS、域名、OpenClaw、Celery Beat、定时任务

## 13. 提交与推送

- [x] 执行 `git status --short`
- [x] 确认只包含本轮代码与文档变更
- [x] 执行 `git add backend docs`
- [x] 执行 `git commit -m "Implement Celery async crawl queue"`
- [x] 执行 `git push`

## 下一轮建议

- [x] 如果异步抓取稳定，下一轮实现 Celery Beat 定时抓取
- [x] 如果 worker 内存偏高，下一轮优化抓取分页、响应大小和任务分批
- [x] 如果任务状态体验不足，下一轮补充任务历史表或任务审计表
