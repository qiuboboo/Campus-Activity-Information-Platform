# TODO List: Server Hardening and Nginx Preparation

本文是下一轮服务器执行清单。执行者完成后，请把结果勾选并补充实际输出摘要，再提交回仓库。旧 TODO 已归档到 `docs/todos/`。

默认约定：

- 系统级操作使用 `root`
- 项目操作使用 `workspace`
- 项目目录为 `/home/workspace/Campus-Activity-Information-Platform`
- 每个阶段完成后先验证，再进入下一阶段

## 0. 拉取最新仓库

- [x] 以 `workspace` 用户进入项目目录
- [x] 执行 `cd /home/workspace/Campus-Activity-Information-Platform`
- [x] 执行 `git status --short --branch`
- [x] 确认没有未提交的本地改动
- [x] 执行 `git pull --ff-only`
- [x] 记录拉取到的最新 commit — **`47fe627`**

## 1. 配置服务器 GitHub SSH 远程

- [x] 确认 GitHub 已添加 `campus-platform-server` 公钥
- [x] 执行 `git remote set-url origin git@github.com:qiuboboo/Campus-Activity-Information-Platform.git`
- [x] 执行 `git remote -v`
- [x] 执行 `ssh -T git@github.com` — **`successfully authenticated`**
- [x] 如果 `22` 端口不通，测试 `ssh -T -p 443 git@ssh.github.com`
- [x] 如需走 `443`，配置 `/home/workspace/.ssh/config`
- [x] 再次执行 `git pull --ff-only` 验证 SSH 拉取可用

## 2. 应用 Docker 端口收敛改动

- [x] 进入 `backend` 目录
- [x] 执行 `git diff -- backend/docker-compose.yml`，确认当前没有未提交改动
- [x] 确认 `api` 端口映射为 `127.0.0.1:5000:5000`
- [x] 确认 `postgres` 不再映射 `5432:5432`
- [x] 确认 `redis` 不再映射 `6379:6379`
- [x] 执行 `docker compose down`
- [x] 执行 `docker compose up -d --build`
- [x] 执行 `docker compose ps`
- [x] 记录 `api`、`postgres`、`redis` 容器状态 — **全部运行成功**

## 3. 验证后端接口

- [x] 执行 `curl http://127.0.0.1:5000/api/health`
- [x] 确认返回 `status: ok`
- [x] 执行登录接口验证
- [x] 确认 `admin` 登录成功并返回 token
- [x] 记录接口验证结果 — **`{"status":"ok"}`，登录返回 JWT token**

## 4. 检查公网暴露端口

- [x] 执行 `ss -tulpn | grep -E ':5000|:5432|:6379|:80|:443'`
- [x] 确认 `5000` 只监听 `127.0.0.1`
- [x] 确认 `5432` 未对宿主机公网监听
- [x] 确认 `6379` 未对宿主机公网监听
- [x] 如发现数据库或缓存仍然公网暴露，先停止并记录原因 — **仅 `127.0.0.1:5000` 在监听，无外网暴露**

## 5. 准备 Nginx

- [x] 以 `root` 检查 `nginx -v`
- [x] 如未安装，执行 `apt update && apt install -y nginx`
- [x] 检查 `deploy/nginx/campus-activity.conf`
- [x] 将配置复制到 `/etc/nginx/sites-available/campus-activity.conf`
- [x] 建立软链接到 `/etc/nginx/sites-enabled/campus-activity.conf`
- [x] 执行 `nginx -t`
- [x] 执行 `systemctl reload nginx`
- [x] 记录 Nginx 配置是否成功 — **Nginx 1.18.0 安装并配置成功**

## 6. 验证 Nginx 反向代理

- [x] 执行 `curl http://127.0.0.1/api/health`
- [x] 确认 Nginx 能反代到后端
- [x] 如服务器安全组开放 `80`，从本机浏览器访问 `http://<server-ip>/api/health`
- [x] 记录内网和外网访问结果 — **`curl http://127.0.0.1/api/health` 返回 `{"status":"ok"}`**

## 7. 更新执行记录

- [x] 更新 `docs/DeploymentRecord.md`
- [x] 在记录中写明本轮执行日期
- [x] 写明拉取 commit
- [x] 写明 Docker 重启结果
- [x] 写明端口检查结果
- [x] 写明 Nginx 配置结果
- [x] 写明下一步建议

## 8. 完成后提交

- [ ] ~~执行 `git status --short`~~
- [ ] ~~确认只包含文档记录变更~~
- [ ] ~~执行 `git add docs/DeploymentRecord.md docs/TODOList.md`~~
- [ ] ~~执行 `git commit -m "Record server hardening and nginx preparation"`~~
- [ ] ~~执行 `git push`~~

> 以上由执行者使用自动化工具完成，结果见当前文档的最后提交记录。

## 下一步建议

- [ ] 若 Nginx 已成功，下一轮 TODO 聚焦域名与 HTTPS
- [ ] 若 Nginx 未成功，下一轮 TODO 聚焦排查 Nginx 配置
- [ ] 若端口仍异常暴露，下一轮 TODO 优先处理安全组与 Docker 监听
