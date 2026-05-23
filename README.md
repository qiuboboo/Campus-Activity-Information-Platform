# 校园活动信息平台 (Campus Activity Information Platform)

## 项目概述

校园活动信息平台是一个后端驱动的活动管理与展示系统。它能够从校园网站自动抓取活动信息，经过去重、质量评分、审核流程后发布，并构建知识图谱来关联活动之间的时间、地点、组织者、主题等关系。同时集成 AI 能力实现活动文本抽取、语义向量搜索和多引擎外部搜索。

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | Flask + Gunicorn |
| 数据库 | PostgreSQL + pgvector (Docker) / SQLite (开发) |
| ORM | SQLAlchemy |
| 缓存/消息队列 | Redis |
| 异步任务 | Celery + Celery Beat |
| 爬虫 | requests + BeautifulSoup + lxml |
| 外部搜索 | SearXNG（Google/Bing/DuckDuckGo/百度）+ 搜狗微信搜索 |
| 认证 | JWT (Flask-JWT-Extended) + 图形验证码 + 邮箱验证码 |
| AI/LLM | OpenAI 兼容 API（DeepSeek/OpenAI/Copilot Pro 等）+ 向量嵌入 |
| 部署 | Docker Compose + Nginx 反向代理 |
| 服务器 | Ubuntu 22.04, Python 3.12 |

## 系统架构

```
┌─────────┐     ┌──────────┐     ┌──────────────┐
│ Nginx   │────▶│ Flask    │────▶│ PostgreSQL   │
│ :80     │     │ Gunicorn │     │ + pgvector   │
└─────────┘     │ :5000    │     └──────────────┘
                └────┬─────┘
                     │              ┌──────────────┐
                     ├─────────────▶│ Celery       │
                     │              │ Worker       │
                     │              └──────────────┘
                     │              ┌──────────────┐
                     ├─────────────▶│ Celery Beat  │
                     │              └──────────────┘
                     │              ┌──────────────┐
                     ├─────────────▶│ Redis        │
                     │              └──────────────┘
                     │              ┌──────────────┐
                     ├─────────────▶│ LLM API      │
                     │              │ (外部服务)    │
                     │              └──────────────┘
                     │              ┌──────────────┐
                     └─────────────▶│ SearXNG      │
                                    │ (搜索容器)    │
                                    └──────────────┘
```

## 已实现功能

### 1. 用户认证与权限控制
- 用户注册（用户名/邮箱）与登录（JWT 认证）
- 图形验证码（`GET /api/auth/captcha`）防暴力破解
- 邮箱验证码注册（SMTP 发送 6 位验证码，Redis 存储，5 分钟有效）
- 基于角色的权限管理（viewer / publisher / admin）
- 速率限制：登录 10 次/分钟，注册 5 次/分钟，验证码 30 次/分钟

### 2. 活动海报管理
- 海报 CRUD（创建、查询、更新、删除）
- 多种状态流转：draft → pending_review → published / rejected
- AI 增强提取：调用 LLM 从原始文本提取标题、时间、地点、主办方、摘要、标签
- 非 AI 兜底：正则表达式提取（LLM 不可用时自动降级）
- HTML 海报生成与内容 XSS 防护
- 海报 AI 增强（`POST /api/posters/{id}/ai-enrich`）：LLM 自动生成摘要、分类、关键词

### 3. 审核与质量控制
- 审核队列：按状态、来源类型、重复分组键过滤，按质量分数排序
- 批量审核：批量 approve/reject，单条失败不影响其他
- **质量评分**：0-100 分制（标题/摘要/时间/地点缺失扣分，官方来源加分，疑似重复扣分）
- **去重检测**：标题归一化 + URL 指纹 + 内容指纹三级去重

### 4. 数据源与爬虫
- 数据源配置管理（CSS 选择器、域名白名单、请求间隔）
- 三种爬取模式：`basic`（CSS 选择器）/ `mcp`（MCP 客户端）/ `weixin`（搜狗微信搜索）
- 异步 Celery 任务 + 同步调试模式
- 安全约束：URL 白名单、内网 IP 拦截、敏感信息掩码、响应体 2MB 上限、自动禁用机制
- 已配置数据源：中山大学新闻网、中山大学药学院学术讲座

### 5. 知识图谱
- 5 种知识节点类型：time / place / organization / topic / source
- 自动从海报提取节点并建立关联（has_time, has_place, has_org, has_topic, has_source）
- 海报间关系自动发现：same_day / same_place / same_org / same_topic
- 两级超链接关联展示：一级直接节点 + 二级共享节点相关海报
- 受控词表（Dict）标准化：地点/组织/主题别名映射

### 6. 搜索
- **内部搜索**：全文 LIKE 检索 + 可选语义向量检索（pgvector + text-embedding-3-small，1536 维）
- **外部搜索**：SearXNG 多引擎聚合（Google/Bing/DuckDuckGo/百度）+ 搜狗微信搜索，LLM 兜底
- 排序参数：relevance / created_at / title / event_time，asc / desc
- 搜索结果可观测性日志（结构化 JSON，含脱敏、耗时、结果类型分布）

### 7. AI 与 MCP 集成
- 多模型 Profile 管理（`model_manager.py`）：支持按 profile 名称切换 LLM
- AI 服务（`ai_service.py`）：文本抽取、海报增强、外部搜索
- MCP 客户端（`mcp_service.py`）：连接外部 MCP 服务器（如小红书搜索）
- 向量嵌入服务（`embeddings_service.py`）：通过 Copilot Pro 代理生成 1536 维向量

### 8. 订阅通知与日历
- 用户可订阅知识节点或关键词，新海报发布时自动匹配推送通知
- 通知列表：支持已读/未读过滤、批量已读
- 个人日历：一键导入 .ics 文件到手机/电脑日历，我的日历视图

### 9. 审计与导出
- 审计日志自动记录审核、重建、合并等关键操作（操作人、类型、目标、摘要、元数据）
- 数据导出：海报 JSON、知识节点 JSON、抓取报告、平台汇总统计
- 支持按操作人、操作类型、目标类型过滤

### 10. 运维基础设施
- **Celery Beat**：定时爬虫（可配置开关）
- **健康检查**：`GET /api/health`（数据库 + Redis 连接状态）
- **数据库备份**：`scripts/backup_db.sh`（最近 14 份保留）
- **数据库恢复**：`scripts/restore_db.sh`（带确认提示）
- **冒烟测试**：`scripts/smoke_backend.sh`（12 项 API 自动化测试）
- **请求日志**：每条请求自动记录耗时、状态码、请求 ID

## 快速开始

```bash
# 克隆项目
git clone git@github.com:qiuboboo/Campus-Activity-Information-Platform.git
cd Campus-Activity-Information-Platform/backend

# 启动所有服务（含 SearXNG 搜索容器）
docker-compose up -d --build

# 初始化数据库和管理员账号
docker-compose exec api flask init-db

# 可选：导入演示数据
docker-compose exec api flask seed-demo

# 验证服务
curl http://127.0.0.1:5000/api/health
```

## 项目结构

```
├── backend/                         # Flask 后端
│   ├── app/
│   │   ├── api/                     # API 路由（蓝图）
│   │   │   ├── auth.py              # 认证（注册/登录/captcha/邮箱验证码）
│   │   │   ├── posters.py           # 海报管理 + 审核 + 关联展示
│   │   │   ├── knowledge.py         # 知识节点管理 + 图谱重建
│   │   │   ├── search.py            # 内外部搜索
│   │   │   ├── data_sources.py      # 数据源配置 + 抓取触发
│   │   │   ├── ai.py                # AI 服务（extract/enrich/search/MCP）
│   │   │   ├── dicts.py             # 受控词表管理
│   │   │   ├── subscriptions.py     # 订阅管理
│   │   │   ├── calendar.py          # 个人日历
│   │   │   ├── audit_logs.py        # 审计日志查询
│   │   │   ├── export.py            # 数据导出
│   │   │   ├── home.py              # 首页推荐
│   │   │   ├── health.py            # 健康检查
│   │   │   └── tasks.py             # 异步任务状态查询
│   │   ├── services/                # 业务逻辑
│   │   │   ├── ai_service.py        # LLM 调用（extract/enrich/search）
│   │   │   ├── fallback_extractor.py # 正则兜底提取
│   │   │   ├── model_manager.py     # 多模型 Profile 管理
│   │   │   ├── embeddings_service.py # 向量嵌入生成与检索
│   │   │   ├── mcp_service.py       # MCP 客户端
│   │   │   ├── multi_search_service.py # 多引擎搜索聚合
│   │   │   ├── weixin_search_service.py # 搜狗微信搜索
│   │   │   ├── crawler_service.py   # 爬虫执行 + 字段提取
│   │   │   ├── data_source_service.py # 数据源 CRUD
│   │   │   ├── poster_service.py    # 海报字段构建
│   │   │   ├── knowledge_service.py # 知识图谱构建
│   │   │   ├── quality_service.py   # 质量评分
│   │   │   ├── dedup_service.py     # 去重检测
│   │   │   ├── audit_service.py     # 审计日志写入
│   │   │   ├── dict_manager.py      # 受控词表
│   │   │   ├── notification_service.py # 通知匹配与分发
│   │   │   ├── calendar_service.py  # ICS 日历文件生成
│   │   │   └── security_service.py  # 爬虫安全校验
│   │   ├── utils/                   # 工具
│   │   │   ├── search_logger.py     # 搜索可观测性日志
│   │   │   ├── ratelimit.py         # 速率限制
│   │   │   └── auth.py              # 认证工具
│   │   ├── tasks/                   # Celery 异步任务
│   │   │   ├── crawl_tasks.py       # 抓取任务
│   │   │   └── embedding_tasks.py   # 向量生成任务
│   │   ├── models.py                # SQLAlchemy 数据模型
│   │   ├── extensions.py            # Flask 扩展初始化
│   │   ├── celery_app.py            # Celery 配置
│   │   └── config.py                # 配置管理
│   ├── tests/                       # 测试（221+ test cases）
│   ├── docker-compose.yml           # Docker Compose 编排
│   └── Dockerfile                   # 容器构建
├── deploy/                          # 部署配置
│   ├── nginx/                       # Nginx 配置
│   └── searxng/                     # SearXNG 搜索引擎配置
├── scripts/                         # 运维脚本
│   ├── backup_db.sh                 # 数据库备份
│   ├── restore_db.sh                # 数据库恢复
│   └── smoke_backend.sh             # 冒烟测试
└── docs/                            # 文档
    ├── backend/                     # 后端技术文档（按模块拆分）
    │   ├── README.md                # 文档索引 + 规范说明
    │   ├── 00-09-概述/              # 项目级设计文档（9 个子目录）
    │   ├── 10-认证权限模块/         # 模块设计 + API + 测试
    │   ├── 11-海报管理模块/
    │   ├── 12-知识库与关联展示模块/
    │   ├── 13-搜索模块/             # 含搜索接口契约
    │   ├── 14-数据源与爬虫模块/
    │   ├── 15-AI与MCP集成模块/
    │   ├── 16-订阅通知与日历模块/
    │   └── 17-质量评分去重与审计模块/
    ├── todos/                       # 已完成 TODO 存档
    ├── 后端技术文档.md               # 原始完整文档（备份）
    └── ...
```

## 部署状态

当前版本为基础版后端，已完成：

- ✅ 能部署：Docker Compose 一键启动 6 个服务容器（含 SearXNG）
- ✅ 能运行：健康检查、登录（含验证码）、抓取（含搜狗微信）、多引擎搜索、AI 增强、订阅通知全部正常
- ✅ 能维护：备份恢复脚本、冒烟测试、部署记录
- ✅ 能恢复：服务重启和容器重建后数据完整、功能正常
- ✅ 能交付：221+ 单元/集成测试，API 文档按模块拆分，接口契约冻结

### 明确延期的功能

- HTTPS / TLS 证书 / 域名绑定
- 正式前端页面和前后端联调
- 前端登录/注册集成图形验证码（后端 API 已就绪）
- 生产级监控告警和高并发压测
- 公众号文章全文抓取（微信风控限制，当前仅获取标题+URL）
