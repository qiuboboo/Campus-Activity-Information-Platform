# TODO List: Server Memory Stabilization and Swap Setup

本文是下一轮服务器执行清单。目标是排查服务器内存占用过高的问题，创建可持久化 swap，并给后端 Docker 服务增加基础内存治理。此轮只处理稳定性，不新增业务功能。

默认约定：

- 项目操作使用 `workspace`
- 需要系统级操作时使用 `sudo`
- 项目目录为 `/home/workspace/Campus-Activity-Information-Platform`
- 后端通过 Docker Compose 运行
- 本轮不处理 HTTPS、域名、证书、OpenClaw、前端页面、Celery 新功能
- 所有执行结果记录到 `docs/DeploymentRecord.md`

## 0. 拉取与检查

- [x] 以 `workspace` 用户进入项目目录
- [x] 执行 `cd /home/workspace/Campus-Activity-Information-Platform`
- [x] 执行 `git status --short --branch`
- [x] 确认没有未提交本地改动
- [x] 执行 `git pull --ff-only`
- [x] 记录起始 commit

## 1. 内存现状诊断

- [x] 执行 `free -h`
- [x] 执行 `swapon --show`
- [x] 执行 `df -h /`
- [x] 执行 `docker stats --no-stream`
- [x] 执行 `ps aux --sort=-%mem | head -20`
- [x] 执行 `docker compose -f backend/docker-compose.yml ps`
- [x] 记录总内存、已用内存、可用内存、swap 状态
- [x] 记录占用内存最高的进程或容器
- [x] 如果根分区可用空间小于 `5G`，暂停创建大 swap，先记录磁盘风险

## 2. 创建 2G swap 文件

- [x] 确认当前没有已有 swap，或已有 swap 明显不足
- [x] 执行 `sudo fallocate -l 2G /swapfile`
- [x] 如果 `fallocate` 失败，改用 `sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress`
- [x] 执行 `sudo chmod 600 /swapfile`
- [x] 执行 `sudo mkswap /swapfile`
- [x] 执行 `sudo swapon /swapfile`
- [x] 执行 `swapon --show`
- [x] 执行 `free -h`
- [x] 确认 swap 已启用且大小约为 `2G`

## 3. 设置开机自动挂载 swap

- [x] 备份 fstab：`sudo cp /etc/fstab /etc/fstab.bak.$(date +%Y%m%d%H%M%S)`
- [x] 检查 `/etc/fstab` 是否已有 `/swapfile`
- [x] 如果没有，执行 `echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab`
- [x] 执行 `sudo mount -a`
- [x] 执行 `swapon --show`
- [x] 确认无报错

## 4. 调整 swap 使用倾向

- [x] 查看当前值：`cat /proc/sys/vm/swappiness`
- [x] 临时设置：`sudo sysctl vm.swappiness=10`
- [x] 持久化设置：`echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-campus-platform.conf`
- [x] 执行 `sudo sysctl --system`
- [x] 再次确认：`cat /proc/sys/vm/swappiness`

## 5. 检查 Docker 与后端内存风险

- [x] 执行 `cd /home/workspace/Campus-Activity-Information-Platform/backend`
- [x] 执行 `docker compose ps`
- [x] 执行 `docker stats --no-stream`
- [x] 执行 `docker compose logs --tail=100 api`
- [x] 检查是否出现 `Killed`、`OOM`、`Out of memory`、容器频繁重启
- [x] 如果 API 内存持续过高，记录 Gunicorn worker/thread 数
- [x] 检查 `backend/gunicorn.conf.py` 中当前 `workers`、`threads`、`preload_app`

## 6. 可选降低 Gunicorn 内存占用

仅当服务器内存较小且 API 容器占用明显过高时执行。

- [x] 将 `backend/gunicorn.conf.py` 的 `workers` 从 `2` 调整为 `1`
- [x] 保持 `threads = 2`
- [x] 保持 `preload_app = True`
- [x] 执行 `docker compose up -d --build`
- [x] 执行 `docker compose ps`
- [x] 执行 `docker stats --no-stream`
- [x] 确认 API 仍可访问：`curl http://127.0.0.1/api/health`
- [x] 如果修改了代码或配置，提交到 Git

## 7. 可选添加 Compose 内存保护说明

如果当前 Docker Compose 版本支持内存限制，可评估添加；如果不确定，先只写文档不强行修改。

- [x] 记录 `docker compose version`
- [x] 判断是否适合在 `backend/docker-compose.yml` 为 `api` 增加 `mem_limit`
- [x] 判断是否适合为 `postgres` 和 `redis` 增加保守 `mem_limit`
- [x] 如果添加限制，先在服务器验证容器能正常启动
- [x] 如果不添加限制，在 `DeploymentRecord.md` 写明原因

## 8. 重启验证

- [x] 执行 `sudo reboot`
- [x] 重连服务器
- [x] 执行 `swapon --show`
- [x] 执行 `free -h`
- [x] 执行 `docker ps`
- [x] 执行 `curl http://127.0.0.1/api/health`
- [x] 确认 swap 重启后仍自动启用
- [x] 确认后端服务重启后正常

## 9. 压力与观察

- [x] 连续执行 3 次 `docker stats --no-stream`，每次间隔约 30 秒
- [x] 触发一次真实站点爬虫或查询已有抓取结果
- [x] 再次执行 `free -h`
- [x] 再次执行 `docker stats --no-stream`
- [x] 记录 swap 是否被大量使用
- [x] 如果 swap 使用持续增长且内存仍紧张，记录下一步需要减少服务或升级配置

## 10. 更新记录

- [x] 更新 `docs/DeploymentRecord.md`
- [x] 写明服务器内存与 swap 初始状态
- [x] 写明创建的 swap 大小与路径
- [x] 写明 `/etc/fstab` 持久化结果
- [x] 写明 `vm.swappiness` 设置
- [x] 写明 Docker 容器内存占用观察结果
- [x] 写明是否调整 Gunicorn 配置
- [x] 写明是否调整 Docker Compose 内存限制
- [x] 写明重启后验证结果
- [x] 明确记录本轮未处理 HTTPS、域名、OpenClaw、Celery 新功能

## 11. 提交与推送

- [x] 执行 `git status --short`
- [x] 确认只包含本轮文档和必要配置变更
- [x] 执行 `git add docs backend/gunicorn.conf.py backend/docker-compose.yml`
- [x] 执行 `git commit -m "Document server swap and memory stabilization"`
- [x] 执行 `git push`

## 下一轮建议

- [x] 如果内存稳定，下一轮再实现 Celery 异步抓取任务
- [x] 如果 API 仍 OOM，下一轮优先减少 Gunicorn worker 或拆分数据库
- [x] 如果磁盘紧张，下一轮处理日志清理、Docker 镜像清理和备份策略
