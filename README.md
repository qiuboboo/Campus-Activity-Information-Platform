# 校园活动信息平台 (Campus Activity Information Platform)

## 项目概述

校园活动信息平台是一个后端驱动的活动管理与展示系统。它能够从校园网站自动抓取活动信息，经过去重、质量评分、审核流程后发布，并构建知识图谱来关联活动之间的时间、地点、组织者、主题等关系。

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | Flask + Gunicorn |
| 数据库 | PostgreSQL (Docker) / SQLite (开发) |
| ORM | SQLAlchemy |
| 缓存/消息队列 | Redis |
| 异步任务 | Celery + Celery Beat |
| 爬虫 | requests + BeautifulSoup |
| 认证 | JWT (Flask-JWT-Extended) |
| 部署 | Docker Compose + Nginx 反向代理 |
| 服务器 | Ubuntu 22.04, Python 3.12 |

## 系统架构

```
┌─────────┐     ┌──────────┐     ┌──────────────┐
│ Nginx   │────▶│ Flask    │────▶│ PostgreSQL   │
│ :80     │     │ Gunicorn │     │ :5432        │
└─────────┘     │ :5000    │     └──────────────┘
                └────┬─────┘
                     │              ┌──────────────┐
                     ├─────────────▶│ Celery       │
                     │              │ Worker       │
                     │              └──────────────┘
                     │              ┌──────────────┐
                     ├─────────────▶│ Celery       │
                     │              │ Beat         │
                     │              └──────────────┘
                     │              ┌──────────────┐
                     └─────────────▶│ Redis        │
                                    │ :6379        │
                                    └──────────────┘
```

## 已实现功能

### 1. 用户认证与权限控制
- 用户注册与登录（JWT 认证）
- 基于角色的权限管理（viewer / publisher / admin）
- 管理员可执行审核、抓取、管理数据源等操作

### 2. 活动海报管理
- 海报的创建、查询、更新、删除
- 支持标题、正文、摘要、活动时间、地点、组织者等字段
- 多种状态流转：草稿 → 审核 → 已发布 / 已拒绝

### 3. 数据源与爬虫
- 数据源的创建和管理（CSS 选择器配置）
- 基于 requests + BeautifulSoup 的网页抓取
- 结构化字段提取：标题、活动时间、地点、组织者
- 异步爬虫任务（Celery）和同步调试模式

### 4. 活动治理
- **审核队列**：按状态、来源类型、重复分组键过滤，按质量分数排序
- **批量审核**：批量 approve/reject，单条失败不影响其他
- **重复检测**：两级去重——精确 URL 匹配跳过创建，内容指纹匹配标记为疑似重复
- **质量评分**：0-100 分制，根据标题完整性、摘要、时间、地点、正文长度、是否重复、是否官方来源评分

### 5. 知识图谱
- 自动从海报字段提取时间、地点、组织者、主题、来源等知识节点
- 自动发现活动间关联（同日、同地、同组织者、同主题）
- 知识图谱重建 API（单条和全量）

### 6. 审计日志
- 审核、批量审核、来源合并、知识重建等操作自动记录
- 记录操作者、操作类型、目标、摘要、元数据
- 支持按操作者、操作类型、目标类型过滤

### 7. 搜索
- 全文搜索：跨海报标题、摘要、正文
- 知识节点搜索

### 8. 导出与演示
- 海报导出（不含原文和敏感字段）
- 知识节点导出
- 抓取报告导出
- 平台数据汇总统计

### 9. 运维基础设施
- **定时爬虫**：Celery Beat 每 12 小时自动抓取，可通过环境变量开关
- **数据库备份**：`scripts/backup_db.sh`——从 Docker PostgreSQL 自动备份，保留最近 14 份
- **数据库恢复**：`scripts/restore_db.sh`——带确认提示的安全恢复脚本
- **冒烟测试**：`scripts/smoke_backend.sh`——12 项 API 自动化测试
- **API 文档**：`docs/APIOverview.md`——完整接口文档含 curl 示例

## 快速开始

### 前置条件

- Docker 和 Docker Compose
- Git

### 启动服务

```bash
# 克隆项目
git clone git@github.com:qiuboboo/Campus-Activity-Information-Platform.git
cd Campus-Activity-Information-Platform/backend

# 启动所有服务
docker-compose up -d --build

# 初始化数据库和管理员账号
docker-compose exec api flask init-db

# 可选：导入演示数据
docker-compose exec api flask seed-demo

# 验证服务
curl http://127.0.0.1:5000/api/health
```

### 运行冒烟测试

```bash
./scripts/smoke_backend.sh
```

### 数据库备份与恢复

```bash
# 备份
./scripts/backup_db.sh

# 恢复（需要确认）
./scripts/restore_db.sh /path/to/backup.sql
```

## 项目结构

```
├── backend/                  # Flask 后端
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   ├── auth.py       # 认证接口
│   │   │   ├── posters.py    # 海报接口
│   │   │   ├── knowledge.py  # 知识图谱接口
│   │   │   ├── search.py     # 搜索接口
│   │   │   ├── data_sources.py  # 数据源接口
│   │   │   ├── tasks.py      # 异步任务接口
│   │   │   ├── audit_logs.py # 审计日志接口
│   │   │   ├── export.py     # 导出接口
│   │   │   └── health.py     # 健康检查
│   │   ├── services/         # 业务逻辑
│   │   │   ├── crawler_service.py   # 爬虫服务
│   │   │   ├── dedup_service.py     # 去重服务
│   │   │   ├── quality_service.py   # 质量评分
│   │   │   ├── knowledge_service.py # 知识图谱服务
│   │   │   ├── audit_service.py     # 审计日志服务
│   │   │   └── poster_service.py    # 海报字段构建
│   │   ├── tasks/            # Celery 异步任务
│   │   ├── models.py         # 数据模型
│   │   ├── celery_app.py     # Celery 配置
│   │   └── config.py         # 配置
│   ├── docker-compose.yml    # Docker Compose 编排
│   └── Dockerfile            # 容器构建
├── scripts/                  # 运维脚本
│   ├── smoke_backend.sh      # 冒烟测试
│   ├── backup_db.sh          # 数据库备份
│   └── restore_db.sh         # 数据库恢复
├── docs/                     # 文档
│   ├── APIOverview.md        # API 总览
│   ├── APIExamples.md        # API 示例
│   ├── DeploymentRecord.md   # 部署记录
│   └── todos/                # 已完成 TODO 存档
└── deploy/                   # 部署配置
    └── nginx/                # Nginx 配置
```

## 部署状态

当前版本为基础版后端，已完成以下目标：

- ✅ **能部署**：Docker Compose 一键启动 5 个服务容器
- ✅ **能运行**：健康检查、登录、抓取、审核、搜索、导出全部正常
- ✅ **能维护**：有备份恢复脚本、部署记录、冒烟测试
- ✅ **能恢复**：服务重启和容器重建后数据完整、功能正常
- ✅ **能交付**：API 文档完整，可支持前端或演示脚本接入

### 明确延期的功能

- HTTPS / TLS 证书 / 域名绑定
- 正式前端页面和前后端联调
- OpenClaw 大模型视觉分析
- 多用户复杂后台管理界面
- 生产级监控告警和高并发压测
- Celery Beat 定时抓取（默认关闭，需手动开启）
