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

- [ ] 以 `workspace` 用户进入项目目录
- [ ] 执行 `cd /home/workspace/Campus-Activity-Information-Platform`
- [ ] 执行 `git status --short --branch`
- [ ] 确认没有未提交本地改动
- [ ] 执行 `git pull --ff-only`
- [ ] 记录起始 commit

## 1. 内存现状诊断

- [ ] 执行 `free -h`
- [ ] 执行 `swapon --show`
- [ ] 执行 `df -h /`
- [ ] 执行 `docker stats --no-stream`
- [ ] 执行 `ps aux --sort=-%mem | head -20`
- [ ] 执行 `docker compose -f backend/docker-compose.yml ps`
- [ ] 记录总内存、已用内存、可用内存、swap 状态
- [ ] 记录占用内存最高的进程或容器
- [ ] 如果根分区可用空间小于 `5G`，暂停创建大 swap，先记录磁盘风险

## 2. 创建 2G swap 文件

- [ ] 确认当前没有已有 swap，或已有 swap 明显不足
- [ ] 执行 `sudo fallocate -l 2G /swapfile`
- [ ] 如果 `fallocate` 失败，改用 `sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress`
- [ ] 执行 `sudo chmod 600 /swapfile`
- [ ] 执行 `sudo mkswap /swapfile`
- [ ] 执行 `sudo swapon /swapfile`
- [ ] 执行 `swapon --show`
- [ ] 执行 `free -h`
- [ ] 确认 swap 已启用且大小约为 `2G`

## 3. 设置开机自动挂载 swap

- [ ] 备份 fstab：`sudo cp /etc/fstab /etc/fstab.bak.$(date +%Y%m%d%H%M%S)`
- [ ] 检查 `/etc/fstab` 是否已有 `/swapfile`
- [ ] 如果没有，执行 `echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab`
- [ ] 执行 `sudo mount -a`
- [ ] 执行 `swapon --show`
- [ ] 确认无报错

## 4. 调整 swap 使用倾向

- [ ] 查看当前值：`cat /proc/sys/vm/swappiness`
- [ ] 临时设置：`sudo sysctl vm.swappiness=10`
- [ ] 持久化设置：`echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-campus-platform.conf`
- [ ] 执行 `sudo sysctl --system`
- [ ] 再次确认：`cat /proc/sys/vm/swappiness`

## 5. 检查 Docker 与后端内存风险

- [ ] 执行 `cd /home/workspace/Campus-Activity-Information-Platform/backend`
- [ ] 执行 `docker compose ps`
- [ ] 执行 `docker stats --no-stream`
- [ ] 执行 `docker compose logs --tail=100 api`
- [ ] 检查是否出现 `Killed`、`OOM`、`Out of memory`、容器频繁重启
- [ ] 如果 API 内存持续过高，记录 Gunicorn worker/thread 数
- [ ] 检查 `backend/gunicorn.conf.py` 中当前 `workers`、`threads`、`preload_app`

## 6. 可选降低 Gunicorn 内存占用

仅当服务器内存较小且 API 容器占用明显过高时执行。

- [ ] 将 `backend/gunicorn.conf.py` 的 `workers` 从 `2` 调整为 `1`
- [ ] 保持 `threads = 2`
- [ ] 保持 `preload_app = True`
- [ ] 执行 `docker compose up -d --build`
- [ ] 执行 `docker compose ps`
- [ ] 执行 `docker stats --no-stream`
- [ ] 确认 API 仍可访问：`curl http://127.0.0.1/api/health`
- [ ] 如果修改了代码或配置，提交到 Git

## 7. 可选添加 Compose 内存保护说明

如果当前 Docker Compose 版本支持内存限制，可评估添加；如果不确定，先只写文档不强行修改。

- [ ] 记录 `docker compose version`
- [ ] 判断是否适合在 `backend/docker-compose.yml` 为 `api` 增加 `mem_limit`
- [ ] 判断是否适合为 `postgres` 和 `redis` 增加保守 `mem_limit`
- [ ] 如果添加限制，先在服务器验证容器能正常启动
- [ ] 如果不添加限制，在 `DeploymentRecord.md` 写明原因

## 8. 重启验证

- [ ] 执行 `sudo reboot`
- [ ] 重连服务器
- [ ] 执行 `swapon --show`
- [ ] 执行 `free -h`
- [ ] 执行 `docker ps`
- [ ] 执行 `curl http://127.0.0.1/api/health`
- [ ] 确认 swap 重启后仍自动启用
- [ ] 确认后端服务重启后正常

## 9. 压力与观察

- [ ] 连续执行 3 次 `docker stats --no-stream`，每次间隔约 30 秒
- [ ] 触发一次真实站点爬虫或查询已有抓取结果
- [ ] 再次执行 `free -h`
- [ ] 再次执行 `docker stats --no-stream`
- [ ] 记录 swap 是否被大量使用
- [ ] 如果 swap 使用持续增长且内存仍紧张，记录下一步需要减少服务或升级配置

## 10. 更新记录

- [ ] 更新 `docs/DeploymentRecord.md`
- [ ] 写明服务器内存与 swap 初始状态
- [ ] 写明创建的 swap 大小与路径
- [ ] 写明 `/etc/fstab` 持久化结果
- [ ] 写明 `vm.swappiness` 设置
- [ ] 写明 Docker 容器内存占用观察结果
- [ ] 写明是否调整 Gunicorn 配置
- [ ] 写明是否调整 Docker Compose 内存限制
- [ ] 写明重启后验证结果
- [ ] 明确记录本轮未处理 HTTPS、域名、OpenClaw、Celery 新功能

## 11. 提交与推送

- [ ] 执行 `git status --short`
- [ ] 确认只包含本轮文档和必要配置变更
- [ ] 执行 `git add docs backend/gunicorn.conf.py backend/docker-compose.yml`
- [ ] 执行 `git commit -m "Document server swap and memory stabilization"`
- [ ] 执行 `git push`

## 下一轮建议

- [ ] 如果内存稳定，下一轮再实现 Celery 异步抓取任务
- [ ] 如果 API 仍 OOM，下一轮优先减少 Gunicorn worker 或拆分数据库
- [ ] 如果磁盘紧张，下一轮处理日志清理、Docker 镜像清理和备份策略
