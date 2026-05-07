# TODO List: Backend Basic Version Finalization

> 使用规范：
> 1. 每完成一项，把 `[ ]` 改成 `[x]`
> 2. 在 `[x]` 后补充一句结果，例如：`- [x] 完成数据库备份脚本 - 结果：已生成并验证恢复`
> 3. 全部完成后，把本文件归档到 `docs/todos/`，再创建下一轮 TODO
> 4. 本轮只收口“基础版后端”，暂不处理 HTTPS、域名、证书、OpenClaw、正式前端页面

## 默认约定

- 服务器操作用户：`workspace`
- 项目目录：`/home/workspace/Campus-Activity-Information-Platform`
- 运行方式：Docker Compose
- 当前基础能力：用户登录、角色权限、海报 CRUD、审核发布、知识图谱、搜索、数据源、爬虫、真实 CSE 抓取、Celery 异步队列、活动治理、审计日志、导出接口
- 本轮目标：让基础版后端达到“可稳定部署、可恢复、可验证、可交付演示”的状态

## 0. 拉取与基线检查

- [ ] 进入服务器项目目录：`cd /home/workspace/Campus-Activity-Information-Platform`
- [ ] 执行 `git status --short --branch`，确认当前分支和未提交改动
- [ ] 执行 `git pull --ff-only` 拉取最新代码
- [ ] 记录当前 commit：`git rev-parse --short HEAD`
- [ ] 检查 Docker Compose 配置：`docker-compose config`
- [ ] 检查服务状态：`docker-compose ps`
- [ ] 执行后端语法检查：`python -m compileall backend`
- [ ] 如果发现本地有未提交改动，不要覆盖，先记录到本 TODO 再处理

## 1. 运行基线盘点

- [ ] 确认 `.env` 或部署环境变量存在，且不提交真实密钥
- [ ] 确认 PostgreSQL、Redis、API、Celery Worker 均能启动
- [ ] 访问健康检查：`curl http://127.0.0.1:8000/health`
- [ ] 登录管理员账号，确认能获取 JWT token
- [ ] 调用 `/api/demo/summary`，记录当前用户数、活动数、知识节点数、抓取日志数
- [ ] 调用 `/api/export/posters.json`，确认导出不包含敏感字段和超长原文
- [ ] 记录当前容器内存占用：`docker stats --no-stream`

## 2. Celery Beat 低频定时抓取

- [ ] 在后端依赖中确认 Celery Beat 可用，如未安装则补充依赖
- [ ] 新增或完善 Celery Beat 启动服务，例如 `celery-beat`
- [ ] 将定时抓取设置为低频任务，建议每 12 小时或每天 1 次
- [ ] 定时任务默认只抓取已启用的数据源
- [ ] 定时任务必须复用现有异步抓取逻辑，不能绕过审计、去重、质量评分
- [ ] 为定时抓取增加开关环境变量，例如 `ENABLE_SCHEDULED_CRAWL=false`
- [ ] 默认生产部署先关闭定时抓取，手动确认后再开启
- [ ] 启动 Beat 后观察日志，确认只注册预期任务，没有高频循环
- [ ] 记录一次手动触发或短周期测试结果，然后恢复低频配置

## 3. 数据库备份与恢复演练

- [ ] 新增数据库备份脚本，例如 `scripts/backup_db.sh`
- [ ] 备份脚本使用 `pg_dump` 从 Docker PostgreSQL 容器导出
- [ ] 备份文件保存到服务器本地目录，例如 `/home/workspace/backups/campus-platform`
- [ ] 备份文件名包含日期和 commit，例如 `campus_2026-05-07_<commit>.sql`
- [ ] 新增恢复脚本或恢复说明，例如 `scripts/restore_db.sh` 或文档命令
- [ ] 恢复流程必须包含“先确认目标库，再执行恢复”的安全提示
- [ ] 执行一次真实备份，记录备份文件大小
- [ ] 使用临时数据库或明确可覆盖的测试库做恢复演练
- [ ] 记录恢复是否成功，不要在生产库上盲目覆盖

## 4. 安全收尾

- [ ] 确认生产环境 `SECRET_KEY` 或 `JWT_SECRET` 不是默认值
- [ ] 确认管理员默认密码已修改
- [ ] 确认 `.env`、数据库密码、JWT 密钥没有被提交到 Git
- [ ] 确认 PostgreSQL 端口未暴露到公网
- [ ] 确认 Redis 端口未暴露到公网
- [ ] 确认 API 当前只开放必要端口
- [ ] 确认服务器防火墙或云安全组仅放行 SSH 和当前需要的 HTTP 测试端口
- [ ] 检查代码中是否存在硬编码 token、密码、私钥
- [ ] 更新文档中的“默认账号/密码”说明，避免公开真实密码

## 5. API 文档冻结

- [ ] 更新或新增 `docs/APIOverview.md`
- [ ] 整理基础版后端核心接口：认证、用户、海报、审核、知识图谱、搜索、数据源、爬虫任务、审计、导出、演示汇总
- [ ] 每类接口至少写清楚方法、路径、用途、是否需要登录
- [ ] 为登录、创建数据源、异步抓取、查询任务状态、审核队列、批量审核、搜索、导出各保留一个 curl 示例
- [ ] 明确基础版暂不承诺的能力：HTTPS、域名、正式前端、OpenClaw、多租户、复杂权限后台
- [ ] 检查文档中的接口路径和当前代码路由一致

## 6. 冒烟测试脚本

- [ ] 新增冒烟测试脚本，例如 `scripts/smoke_backend.sh`
- [ ] 脚本读取环境变量中的 API 地址、管理员账号、管理员密码
- [ ] 测试 `/health`
- [ ] 测试管理员登录并提取 token
- [ ] 测试 `/api/demo/summary`
- [ ] 测试数据源列表接口
- [ ] 测试异步抓取任务提交接口，优先使用低风险测试数据源
- [ ] 测试任务状态查询接口
- [ ] 测试审核队列接口
- [ ] 测试搜索接口
- [ ] 测试导出接口
- [ ] 脚本失败时应输出失败接口和 HTTP 状态码
- [ ] 执行一次冒烟测试，记录结果

## 7. 服务器重启恢复验证

- [ ] 执行 `docker-compose down`
- [ ] 执行 `docker-compose up -d`
- [ ] 等待服务启动后再次访问 `/health`
- [ ] 确认 PostgreSQL 数据仍在
- [ ] 确认 Redis 可用
- [ ] 确认 Celery Worker 可用
- [ ] 如果启用了 Celery Beat，确认 Beat 可用且没有重复任务
- [ ] 记录容器启动后的状态：`docker-compose ps`
- [ ] 如条件允许，执行一次服务器重启后验证：`sudo reboot`
- [ ] 服务器重启后重新连接，确认 Docker 服务和后端服务恢复情况

## 8. 基础版后端验收

- [ ] 至少存在 1 个管理员账号可登录
- [ ] 至少存在 1 个真实数据源
- [ ] 至少完成 1 次真实 CSE 网站抓取或保留已有抓取记录
- [ ] 抓取结果进入草稿或待审核状态
- [ ] 审核通过后活动可发布
- [ ] 发布活动能参与搜索
- [ ] 发布活动能生成或关联知识图谱节点
- [ ] 审计日志能记录审核或批量审核操作
- [ ] 导出接口可返回海报、知识图谱、抓取报告
- [ ] 内存占用稳定，不再出现明显 OOM 或容器反复重启

## 9. 更新记录、提交与推送

- [ ] 更新 `docs/DeploymentRecord.md`，记录本轮完成内容、验证命令、剩余风险
- [ ] 将完成后的 `docs/TODOList.md` 归档到 `docs/todos/YYYY-MM-DD-backend-basic-finalization.md`
- [ ] 创建下一轮新的 `docs/TODOList.md`
- [ ] 执行 `git diff --check`
- [ ] 执行 `git status --short`
- [ ] 提交代码：`git add ... && git commit -m "Finalize backend basic deployment"`
- [ ] 推送代码：`git push`

## 验收口径

基础版后端完成的判断标准不是“所有想法都做完”，而是：

- 能部署：Docker Compose 一键启动核心服务
- 能运行：健康检查、登录、抓取、审核、搜索、导出正常
- 能维护：有备份恢复路径、有部署记录、有冒烟测试
- 能恢复：服务重启或服务器重启后可验证恢复
- 能交付：API 文档足够让后续前端或演示脚本接入

## 明确延期

- HTTPS、域名绑定、SSL 证书
- 正式前端页面和前后端联调
- OpenClaw 或其他大模型视觉分析生产接入
- 多用户复杂后台管理界面
- 高并发压测和生产级监控告警
