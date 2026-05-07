# Next Task Plan: Celery Async Crawl Queue

本文是 swap 与内存治理完成后的下一轮候选任务规划。当前 `docs/TODOList.md` 仍应优先执行服务器内存稳定化；确认 swap 生效、Docker 内存稳定后，再把本文内容旋转为新的正式 TODO。

## 目标

将当前同步执行的 `POST /api/data-sources/{id}/crawl` 改造为异步任务模式：

- API 只负责提交抓取任务，不在请求线程中直接抓网页
- Celery Worker 从 Redis 队列消费任务
- 前端或调用方可查询任务状态
- 抓取日志继续写入 `crawl_logs`
- 默认控制并发，避免服务器内存再次飙升

## 默认约定

- 先完成当前 swap 任务，再执行本计划
- 本轮不接入 OpenClaw
- 本轮不做定时任务，只做手动触发的异步任务
- Worker 初始并发设置为 `1`
- 继续使用现有 Redis 容器作为 broker
- 继续保持现有同步抓取函数可复用，避免大改业务逻辑

## 建议实现范围

### 1. Celery 应用初始化

- 新增 `backend/app/celery_app.py`
- 从 Flask `Config.REDIS_URL` 读取 broker 与 result backend
- 确保 Celery task 内可以访问 Flask app context
- 避免在 worker import 时重复触发数据库建表竞态

### 2. 抓取任务封装

- 新增 `backend/app/tasks/__init__.py`
- 新增 `backend/app/tasks/crawl_tasks.py`
- 实现 `crawl_data_source_task(data_source_id, user_id)`
- task 内调用现有 `crawl_data_source(data_source_id, user_id)`
- 捕获异常并返回结构化错误

### 3. API 改造

- `POST /api/data-sources/{id}/crawl` 默认改为提交 Celery 任务
- 返回 `202 Accepted`
- 返回 `task_id`
- 返回 `status_url`，例如 `/api/tasks/{task_id}`
- 保留可选同步模式，例如请求体传 `{"sync": true}` 时仍同步执行，便于调试

### 4. 任务状态接口

- 新增 `backend/app/api/tasks.py`
- 注册 tasks 蓝图
- 实现 `GET /api/tasks/{task_id}`
- 返回 `task_id`
- 返回 `state`
- 返回 `result` 或 `error`
- 需要 JWT 登录

### 5. Docker Compose 增加 worker

- 在 `backend/docker-compose.yml` 新增 `worker` 服务
- 使用与 `api` 相同镜像
- command 示例：`celery -A app.celery_app.celery worker --loglevel=INFO --concurrency=1`
- worker 依赖 `postgres` 和 `redis`
- worker 使用同一个 `.env`
- 不暴露端口
- 如 swap 任务中确认内存紧张，暂不增加 beat 或多个 worker

### 6. 内存保护

- Worker 初始并发固定为 `1`
- 记录 worker 启动后 `docker stats --no-stream`
- 抓取真实 CSE 页面后再次记录内存
- 如果 worker 内存高于预期，优先优化抓取代码，不提高并发

### 7. 文档与示例

- 更新 `docs/APIExamples.md`
- 添加异步触发抓取示例
- 添加查询任务状态示例
- 添加同步调试模式示例
- 更新 `docs/DeploymentRecord.md`

## 验收标准

- `docker compose up -d --build` 后存在 `api`、`worker`、`postgres`、`redis`
- `/api/health` 正常
- 登录接口正常
- `POST /api/data-sources/{id}/crawl` 返回 `202` 和 `task_id`
- `GET /api/tasks/{task_id}` 可查询任务状态
- 抓取完成后生成海报草稿
- `crawl_logs` 记录成功或失败
- 真实 CSE 抓取可通过异步任务完成
- Worker 并发为 `1`
- Docker 内存占用记录到 `DeploymentRecord.md`

## 风险与注意

- Celery worker 会增加一个常驻进程，必须先确认 swap 与内存稳定
- 不要在本轮引入 Celery Beat，避免任务定时触发失控
- 不要提高 worker 并发
- 不要把 OpenClaw 放进这一轮
- 如果 Redis 不稳定，优先修 Redis/Compose，不要继续扩展功能

