# TODO List: Next Task

> **使用规范**：
> 1. 每完成一项，将 `[ ]` 改为 `[x]`
> 2. 在 `[x]` 后添加完成状态报告，格式：`✅ 结果：<做了什么>`
> 3. 全部完成后更新 `docs/DeploymentRecord.md`

本文件是当前轮次的任务清单。上一轮活动治理（Activity Governance）已完成，相关记录已归档至 `docs/todos/2026-05-07-activity-governance.md`。

默认约定：

- 项目操作使用 `workspace`
- 项目目录为 `/home/workspace/Campus-Activity-Information-Platform`
- 后端通过 Docker Compose 运行（docker-compose v1.29）
- 已就绪：审核队列、批量审核、重复检测、质量评分、审计日志、知识图谱重建、导出接口
- 仍待定：HTTPS、域名、证书、OpenClaw、前端页面、Celery Beat、定时抓取

```bash
# 当前状态
cd /home/workspace/Campus-Activity-Information-Platform
git status --short --branch
```

## 0. 拉取与检查

- [ ] 执行 `git pull --ff-only`
- [ ] 记录起始 commit
- [ ] 执行 `python -m compileall backend`
