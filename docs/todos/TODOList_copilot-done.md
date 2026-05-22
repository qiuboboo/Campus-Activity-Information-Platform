# TODO List: Copilot Pro 集成与 AI API 测试

> **阶段目标**：接入 Copilot Pro 订阅作为 LLM 后端，用多模型完成 AI API 端到端测试。
> **更新日期**：2026-05-19

## 使用规范

1. 每完成一项，把 `[ ]` 改成 `[x]`
2. 在 `[x]` 后补充一句结果
3. 全部完成后，把本文件归档到 `docs/todos/`

---

## Copilot Pro 代理接入

- [ ] docker-compose 添加 `copilot-proxy` 服务
  - 基于 `node:20-slim` 镜像，启动 `npx copilot-api-node20@latest start --openai`
  - 暴露端口 4141
- [ ] `docker-compose up` 验证代理启动成功
- [ ] 完成 OAuth Device Flow 认证（浏览器打开 URL 输入 code）
- [ ] 验证代理可用：`curl localhost:4141/v1/models`

## .env 模型配置

- [ ] 添加 `LLM_COPILOT_BASE_URL=http://copilot-proxy:4141/v1`
- [ ] 添加 `LLM_COPILOT_MODEL=gpt-4`（根据订阅选择模型）
- [ ] 更新 `.env.example` 添加 Copilot 配置示例
- [ ] 重启 api 容器使新配置生效

## 多模型端点测试

- [ ] `POST /api/ai/extract` 测试 default 模型（DeepSeek）
- [ ] `POST /api/ai/extract` 测试 copilot 模型（传 `"model": "copilot"`）
- [ ] 对比两个模型的结构化提取结果
- [ ] 测试 fallback extractor：断开 API Key 后验证正则降级

## 文档与收尾

- [ ] 更新 `docs/后端技术文档.md` — 环境变量表添加 Copilot Pro 说明
- [ ] 归档本 TODOList

---

## 当前状态

```bash
cd /home/workspace/Campus-Activity-Information-Platform
git status --short --branch
```
