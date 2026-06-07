# Campus Activity Information Platform — AI Collaboration Guide

## 项目概况

校园活动信息平台，后端 Flask + PostgreSQL/pgvector + Redis + Celery，前端 Vue 3 + Element Plus + TypeScript。
目标：校内官方大型活动的采集、结构化、知识关联展示与智能搜索。

## 分层约定

| 层 | 职责 | 可以做什么 | 不能做什么 |
|---|---|---|---|
| `api/` | 参数提取、调用 service、返回 JSON | `request.args.get()`, 调用 service 函数, `jsonify()` | **不能直接操作 `db.session`** |
| `services/` | 业务逻辑 | 操作 `db.session`, 调用外部 API, 数据处理 | 不能直接读 `flask.request` |
| `tasks/` | 异步耗时任务 (Celery) | 调用 service, 长时间运行 | 不能依赖 Flask request 上下文 |
| `models/` | 数据定义 | SQLAlchemy 模型、关系、`to_dict()` | 不能包含业务逻辑 |
| `schemas/` | 请求/响应校验 | Marshmallow schema, 序列化/反序列化 | 不能操作数据库 |
| `utils/` | 通用工具 | 装饰器、辅助函数 | 不能包含业务规则 |

## 目录结构

```
backend/app/
├── api/           # 蓝图，一模块一文件: auth.py, posters.py, knowledge.py ...
├── services/      # 业务逻辑: poster_service.py, knowledge_service.py ...
├── models/        # 数据模型（拆分自原 models.py 单文件）
│   ├── __init__.py
│   ├── user.py
│   ├── poster.py
│   ├── knowledge.py
│   ├── data_source.py
│   └── ...
├── schemas/       # Marshmallow schemas: auth.py, posters.py ...
├── tasks/         # Celery 任务: crawl_tasks.py, ai_tasks.py, index_tasks.py
├── utils/         # 工具: auth.py, ratelimit.py, search_logger.py
├── config.py      # 配置（只放 Config 类，不放业务函数）
├── extensions.py  # Flask 扩展初始化
├── models.py      # 向后兼容的 re-export，逐步废弃
└── __init__.py    # create_app() 工厂函数 + 蓝图注册
```

## API 设计规范

### URL 前缀

```
/api               → health, home
/api/auth          → auth
/api/posters       → posters（含 review-queue, related 等子路由）
/api/knowledge     → knowledge
/api/search        → search
/api/data-sources  → data_sources
/api/subscriptions → subscriptions
/api/calendar      → calendar
/api/ai            → ai
/api/dict          → dicts
/api/export        → export
/api/tasks         → tasks
/api/audit-logs    → audit_logs
```

### 响应 envelope

```python
# 列表 — 统一结构
{"items": [...], "page": 1, "per_page": 10, "total": 30}

# 单项 — 统一结构
{"item": {...}}

# 操作成功（无返回数据）
{"ok": true}

# 错误 — 统一结构
{"error": "Bad Request", "message": "具体错误描述", "code": 400}
```

### 状态码约定

- `200` 成功
- `201` 创建成功
- `400` 参数校验失败
- `401` 未认证
- `403` 权限不足
- `404` 资源不存在
- `409` 冲突（用户名/邮箱已存在等）
- `429` 频率限制
- `500` 服务端错误（由全局 error handler 统一处理）

### 端点命名

- 列表：`GET /api/resource` → `def list_resource()`
- 详情：`GET /api/resource/<id>` → `def get_resource(id)`
- 创建：`POST /api/resource` → `def create_resource()`
- 更新：`PUT /api/resource/<id>` → `def update_resource(id)`
- 删除：`DELETE /api/resource/<id>` → `def delete_resource(id)`

### 蓝图定义

```python
# api/xxx.py
from flask import Blueprint
xxx_bp = Blueprint("xxx", __name__)

@xxx_bp.get("")          # GET /api/resource
@xxx_bp.get("/<int:id>") # GET /api/resource/5
@xxx_bp.post("")         # POST /api/resource
@xxx_bp.put("/<int:id>") # PUT /api/resource/5
@xxx_bp.delete("/<int:id>") # DELETE /api/resource/5
```

## 代码风格

### Type hints — 所有新函数必须加

```python
def get_poster(poster_id: int) -> dict | None:
    ...

def list_posters(page: int, per_page: int, keyword: str = "") -> dict:
    ...
```

### Import 规则

- 模块顶部 import，**禁止函数体内懒加载**
- **例外**：Celery 任务（`from ..tasks.xxx import`）可在条件分支内懒加载，避免测试环境强制初始化 Celery app
- 蓝图内不直接 `from ..extensions import db` 然后 `db.session`，必须通过 service 层
- 跨层调用：`api → service → (model | external)`

### 错误处理

- Service 层抛出异常，API 层通过全局 error handler 统一转换为 JSON
- 不要让 API 端点在每个函数里 `try/except` 然后手动拼 JSON

### 认证装饰器

```python
@jwt_required()                    # 需要登录
@roles_required("admin")           # 需要 admin 角色
@roles_required("publisher", "admin")  # 多角色
```

## 新增功能 checklist

当要加一个新功能模块时，按以下顺序操作：

1. `models/模块名.py` — 建模型（或扩展现有模型）
2. `services/模块名_service.py` — 写纯业务逻辑
3. `schemas/模块名.py` — 定义请求/响应 Marshmallow schema
4. `api/模块名.py` — 定义蓝图，只做参数提取和 service 调用
5. `tasks/模块名_tasks.py` — 如有异步需求
6. `api/__init__.py` 或 `create_app()` — 注册蓝图
7. `tests/` — 加测试

## 测试规范

- API 集成测试优先：每个端点至少一个 happy path + 一个 error case
- Mock 外部依赖：LLM API、MCP、外部 HTTP 请求
- 不 mock 数据库：测试用内存 SQLite
- 测试文件命名：`tests/test_模块名.py`

## 环境变量

见 `backend/.env.example`。敏感信息（API Key、密码等）放 `.env`（已 gitignore），不硬编码，不写进文档。

## 常用命令

```bash
cd backend
python wsgi.py                          # 开发启动
docker compose up -d                    # 完整环境启动
docker compose exec app python -m pytest tests/ -v  # 运行测试
```
