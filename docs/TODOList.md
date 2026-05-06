# TODO List: Data Sources and Basic Crawler Feature Round

本文是下一轮后端功能开发清单。目标是按 `docs/后端技术文档.md` 先实现第一版“数据源配置 + 基础网页抓取 + 抓取日志 + 活动草稿生成”。本轮继续暂不处理 HTTPS、域名、证书、前端页面、OpenClaw、向量搜索和定时任务。

默认约定：

- 项目操作使用 `workspace`
- 项目目录为 `/home/workspace/Campus-Activity-Information-Platform`
- 后端通过 Docker Compose 运行
- 优先保持现有 Flask 项目结构
- 当前阶段继续使用 `AUTO_CREATE_TABLES`
- 本轮只做基础爬虫，不调用 OpenClaw
- 外部网页抓取必须设置超时、限制响应大小，并记录失败原因
- 完成后更新 `docs/DeploymentRecord.md`

## 0. 拉取与检查

- [ ] 以 `workspace` 用户进入项目目录
- [ ] 执行 `cd /home/workspace/Campus-Activity-Information-Platform`
- [ ] 执行 `git status --short --branch`
- [ ] 确认没有未提交本地改动
- [ ] 执行 `git pull --ff-only`
- [ ] 记录起始 commit
- [ ] 执行 `python -m compileall backend`

## 1. 扩展依赖

- [ ] 检查 `backend/requirements.txt`
- [ ] 增加 `requests`
- [ ] 增加 `beautifulsoup4`
- [ ] 如需 URL 解析，优先使用 Python 标准库 `urllib.parse`
- [ ] 不引入 Playwright、Selenium 或浏览器自动化
- [ ] 不引入 OpenClaw 依赖

## 2. 扩展数据库模型

- [ ] 在 `backend/app/models.py` 中新增 `DataSource`
- [ ] 在 `backend/app/models.py` 中新增 `CrawlLog`
- [ ] `DataSource` 至少包含 `name`
- [ ] `DataSource` 至少包含 `base_url`
- [ ] `DataSource` 至少包含 `list_selector`
- [ ] `DataSource` 至少包含 `content_selector`
- [ ] `DataSource` 至少包含 `enabled`
- [ ] `DataSource` 至少包含 `crawl_mode`
- [ ] `CrawlLog` 至少包含 `data_source_id`
- [ ] `CrawlLog` 至少包含 `status`
- [ ] `CrawlLog` 至少包含 `message`
- [ ] `CrawlLog` 至少包含 `started_at`
- [ ] `CrawlLog` 至少包含 `finished_at`
- [ ] 为两个模型实现 `to_dict()`
- [ ] 建立 `DataSource` 与 `CrawlLog` 的 relationship

## 3. 实现数据源服务层

- [ ] 新增 `backend/app/services/data_source_service.py`
- [ ] 实现创建数据源
- [ ] 实现查询数据源列表
- [ ] 实现查询单个数据源
- [ ] 实现更新数据源
- [ ] 实现启用或禁用数据源
- [ ] 实现基础字段校验
- [ ] 校验 `base_url` 必须是 `http://` 或 `https://`
- [ ] 默认 `crawl_mode` 为 `basic`
- [ ] 当前只允许 `basic`，如果收到 `openclaw` 应返回清晰错误或暂不支持说明

## 4. 实现基础抓取服务

- [ ] 新增 `backend/app/services/crawler_service.py`
- [ ] 使用 `requests` 发起 HTTP GET
- [ ] 设置合理超时，例如 `timeout=10`
- [ ] 设置基础 `User-Agent`
- [ ] 限制响应正文最大处理长度，避免异常大页面拖垮服务
- [ ] 使用 `BeautifulSoup` 解析 HTML
- [ ] 使用 `list_selector` 提取列表页链接
- [ ] 支持相对链接转绝对链接
- [ ] 使用 `content_selector` 提取详情页正文
- [ ] 如果 `content_selector` 为空，允许回退到 `body`
- [ ] 对抓取文本做基础清洗，包括去空白、截断和去重
- [ ] 抓取失败时不要让 API 崩溃，应写入失败日志并返回可读错误

## 5. 从抓取内容生成草稿海报

- [ ] 从详情页标题或链接文本生成 `Poster.title`
- [ ] 从详情页正文生成 `Poster.raw_text`
- [ ] 从正文前若干字符生成 `Poster.summary`
- [ ] `Poster.source_type` 设置为 `crawl`
- [ ] `Poster.source_url` 设置为详情页 URL
- [ ] 默认状态为 `draft` 或现有草稿状态
- [ ] 创建人为当前登录用户
- [ ] 避免重复入库相同 `source_url`
- [ ] 本轮不要求自动审核通过
- [ ] 本轮不要求自动建知识图谱，待管理员审核通过后沿用现有审核逻辑

## 6. 实现数据源 API

- [ ] 新增 `backend/app/api/data_sources.py`
- [ ] 在 `backend/app/__init__.py` 注册数据源蓝图
- [ ] 实现 `GET /api/data-sources`
- [ ] 实现 `POST /api/data-sources`
- [ ] 实现 `GET /api/data-sources/{id}`
- [ ] 实现 `PUT /api/data-sources/{id}`
- [ ] 实现 `POST /api/data-sources/{id}/crawl`
- [ ] 实现 `GET /api/data-sources/{id}/logs`
- [ ] 数据源管理接口要求 JWT 登录
- [ ] 创建、更新、抓取接口建议要求 `admin`
- [ ] 返回结构保持 JSON，可直接用于前端管理页

## 7. 更新演示数据与接口示例

- [ ] 更新 `seed-demo`，可选创建 1 个示例数据源
- [ ] 不在 `seed-demo` 中默认访问外网
- [ ] 更新 `docs/APIExamples.md`
- [ ] 添加创建数据源示例
- [ ] 添加触发抓取示例
- [ ] 添加查看抓取日志示例
- [ ] 添加抓取生成草稿后的海报查询示例

## 8. 本地或服务器语法验证

- [ ] 执行 `python -m compileall backend`
- [ ] 如依赖已安装，执行 Flask 启动验证
- [ ] 确认新增蓝图不会影响 `/api/health`
- [ ] 确认登录接口仍可用
- [ ] 确认已有知识图谱接口仍可用

## 9. 服务器 Docker 验证

- [ ] 进入 `backend` 目录
- [ ] 执行 `docker compose down`
- [ ] 执行 `docker compose up -d --build`
- [ ] 执行 `docker compose ps`
- [ ] 确认 `api`、`postgres`、`redis` 均为运行状态
- [ ] 执行 `curl http://127.0.0.1/api/health`
- [ ] 登录并记录 JWT token
- [ ] 创建一个测试数据源
- [ ] 使用一个稳定、可控、内容较小的测试页面验证抓取
- [ ] 如果没有合适外网页面，可临时在服务器起一个本地静态 HTML 页面作为抓取目标
- [ ] 验证抓取成功后生成海报草稿
- [ ] 验证 `crawl_logs` 写入成功日志
- [ ] 验证错误 URL 会写入失败日志

## 10. 更新记录

- [ ] 更新 `docs/DeploymentRecord.md`
- [ ] 写明拉取 commit
- [ ] 写明新增模型与接口
- [ ] 写明依赖变更
- [ ] 写明 Docker 重建结果
- [ ] 写明创建数据源验证结果
- [ ] 写明抓取成功与失败日志验证结果
- [ ] 明确记录 HTTPS、域名、OpenClaw、向量搜索、本轮未处理

## 11. 提交与推送

- [ ] 执行 `git status --short`
- [ ] 确认只包含本轮代码与文档变更
- [ ] 执行 `git add backend docs`
- [ ] 执行 `git commit -m "Implement basic data source crawler"`
- [ ] 执行 `git push`

## 下一轮建议

- [ ] 如果基础爬虫通过，下一轮实现 Celery 异步抓取任务
- [ ] 如果草稿质量不足，下一轮优化规则抽取标题、时间、地点和主办方
- [ ] 如果外网页面复杂，下一轮再评估 OpenClaw 或浏览器自动化
- [ ] HTTPS、域名、证书继续延后
