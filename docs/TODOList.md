# TODO List: AI & MCP 集成阶段

> **阶段目标**：为后端接入 LLM API 和 MCP 协议，替代 OpenClaw 方案。
> **更新日期**：2026-05-19

## 使用规范

1. 每完成一项，把 `[ ]` 改成 `[x]`
2. 在 `[x]` 后补充一句结果
3. 全部完成后，把本文件归档到 `docs/todos/`

---

## 配置与环境

- [x] 更新 `.env.example`，添加 `LLM_API_KEY`、`LLM_API_BASE_URL`、`LLM_MODEL` 变量
- [x] 更新 `config.py`，读取新的环境变量配置
- [x] 安装依赖：`pip install mcp`（Python MCP SDK）

## 爬虫安全改造

- [x] 实现 `validate_target_url()` — URL 白名单、内网地址拦截、协议校验
- [x] 实现 `sanitize_crawled_text()` — XSS 防护、控制字符剥离、敏感信息掩码
- [x] 实现请求限速 — 支持 `request_interval` 配置
- [x] 实现重定向安全校验 — 跨域重定向拦截
- [x] 更新 `data_sources` 模型 — 增加 `allowed_domains`、`request_interval` 字段
- [x] 更新 `data_source_service.py` — 新字段的 CRUD 支持
- [x] 集中安全配置到 `config.py` — 所有爬虫安全参数可配置
- [x] 爬虫安全事件日志与自动禁用机制

## AI Service（ai_service.py）

- [x] 实现 `extract_from_text(raw_text: str) -> dict` — 调用 LLM 从原始文本提取结构化活动信息
- [x] 实现 `enrich_poster(poster_id: int) -> dict` — 对海报做摘要生成、分类标签
- [x] 实现 `search_external(query: str) -> list[dict]` — LLM 驱动的外部搜索
- [x] 实现 LLM 调用的统一客户端（超时、重试、日志）
- [x] 实现非 AI 兜底降级逻辑

## MCP Client（mcp_service.py）

- [x] 实现 `call_mcp(server_name: str, tool: str, params: dict) -> dict` — 通用 MCP 调用接口
- [x] 实现 `search_xiaohongshu(query: str, **kwargs) -> list[dict]` — 小红书搜索封装
- [x] 实现 MCP 服务发现与生命周期管理（启动/关闭 MCP 服务器进程）
- [x] 实现 MCP 调用的错误处理与日志

## AI 统一接口（api/ai.py）

- [x] 创建 `GET /api/ai/status` — 查看 AI 服务状态
- [x] 创建 `POST /api/ai/extract` — AI 活动信息提取
- [x] 创建 `POST /api/ai/enrich/{id}` — AI 海报增强
- [x] 创建 `POST /api/ai/search` — AI 外部搜索
- [x] 创建 `GET /api/ai/mcp/servers` — 查看 MCP 服务器
- [x] 创建 `POST /api/ai/mcp/call` — 调用 MCP 工具

## 集成与验证

- [x] DeepSeek API 配置并验证提取功能
- [x] 冒烟测试 12/12 通过
- [x] 安全模块 9/9 测试通过

---

## 当前文件结构

```
backend/app/
├── __init__.py           # 应用工厂
├── config.py             # 多模型 LLM 配置
├── extensions.py         # db, jwt, cors
├── models.py             # 含 allowed_domains, tags 等新字段
├── celery_app.py         # Celery 配置
├── api/
│   ├── ai.py             # 统一 AI 接口（新增）
│   ├── auth.py           # 登录鉴权
│   ├── posters.py        # 海报 CRUD
│   ├── data_sources.py   # 数据源管理（含 crawl_mode=mcp）
│   ├── health.py         # 健康检查
│   ├── knowledge.py      # 知识图谱
│   ├── search.py         # 内部搜索
│   ├── tasks.py          # 异步任务状态
│   ├── audit_logs.py     # 审计日志
│   └── export.py         # 导出
├── services/
│   ├── ai_service.py     # AI 业务逻辑：提取/增强/搜索（新增）
│   ├── mcp_service.py    # MCP 客户端（新增）
│   ├── security_service.py # 爬虫安全（新增）
│   ├── crawler_service.py  # 爬虫（安全加固 + MCP 模式）
│   ├── data_source_service.py # 数据源（支持新字段）
│   ├── poster_service.py
│   ├── knowledge_service.py
│   ├── quality_service.py
│   ├── dedup_service.py
│   ├── audit_service.py
│   └── bootstrap.py
├── tasks/
│   └── crawl_tasks.py
└── utils/
    └── auth.py
```

## 当前状态

```bash
cd /home/workspace/Campus-Activity-Information-Platform
git status --short --branch
```
