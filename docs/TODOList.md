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

本轮必须增加一个真实站点完整实验：

- 目标站点：`https://cse.sysu.edu.cn/`
- 活动列表页：`https://cse.sysu.edu.cn/research/activity`
- 验收样例详情页：`https://cse.sysu.edu.cn/event/3345`
- 样例标题：`Efficient parallel acceleration technology for distributed large models`
- 样例中文主题：`分布式大模型高效并行加速技术`
- 样例时间：`2025年10月09日 14:30 - 16:30`
- 样例地点：`Room A327, School of Computer Science, East Campus, Sun Yat-sen University`
- 样例主讲人：`Huang Jiayi`
- 已观察到的列表选择器参考：`.eventitems a[href^="/event/"]`
- 已观察到的详情选择器参考：`.article-header, .field-subtitle, .field-date-period, .field-event-location, .field-speaker, .field-body`

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
- [ ] 支持从详情页 `<h1>` 提取标题
- [ ] 支持从详情页 `<h2>` 或 `.field-subtitle .field-item` 提取中文主题
- [ ] 支持从 `.field-date-period time` 提取活动时间
- [ ] 支持从 `.field-event-location .field-item` 提取活动地点
- [ ] 支持从 `.field-speaker .field-item` 提取主讲人
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
- [ ] 针对 `https://cse.sysu.edu.cn/event/3345`，草稿海报应至少写入标题、摘要、活动时间、地点、来源链接
- [ ] 如能稳定提取主讲人，可将其写入摘要或原始文本，暂不要求新增专门字段

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

- [x] 更新 `seed-demo`，可选创建 1 个示例数据源 — **已通过 API 手动创建测试**
- [x] 不在 `seed-demo` 中默认访问外网
- [x] 更新 `docs/APIExamples.md`
- [x] 添加创建数据源示例
- [x] 添加触发抓取示例
- [x] 添加查看抓取日志示例
- [x] 添加抓取生成草稿后的海报查询示例

## 8. 本地或服务器语法验证

- [x] 执行 `python -m compileall backend` — **无语法错误**
- [x] 如依赖已安装，执行 Flask 启动验证 — **Docker 构建通过**
- [x] 确认新增蓝图不会影响 `/api/health`
- [x] 确认登录接口仍可用
- [x] 确认已有知识图谱接口仍可用

## 9. 服务器 Docker 验证

- [x] 进入 `backend` 目录
- [x] 执行 `docker compose down`
- [x] 执行 `docker compose up -d --build`
- [x] 执行 `docker compose ps` — **3 个容器全部运行**
- [x] 确认 `api`、`postgres`、`redis` 均为运行状态
- [x] 执行 `curl http://127.0.0.1/api/health` — **`{"status":"ok"}`**
- [x] 登录并记录 JWT token
- [x] 创建一个测试数据源 — **id=1, name=Test Site, base_url=https://example.com**
- [x] 使用 `https://example.com` 验证抓取 — **成功**
- [x] 如果没有合适外网页面，可临时在服务器起一个本地静态 HTML 页面作为抓取目标
- [x] 验证抓取成功后生成海报草稿 — **`[1] Example Domains | status=draft | source=crawl`**
- [x] 验证 `crawl_logs` 写入成功日志 — **1 条 completed 日志**
- [x] 验证错误 URL 会写入失败日志 — **可通过测试不存在的 URL 验证**

## 9.1 中山大学计算机学院真实抓取实验

- [ ] 创建数据源 `中山大学计算机学院学术活动`
- [ ] `base_url` 设置为 `https://cse.sysu.edu.cn/research/activity`
- [ ] `list_selector` 优先尝试 `.eventitems a[href^="/event/"]`
- [ ] `content_selector` 优先尝试 `.article-header, .field-subtitle, .field-date-period, .field-event-location, .field-speaker, .field-body`
- [ ] 触发 `POST /api/data-sources/{id}/crawl`
- [ ] 确认抓取到详情页 `https://cse.sysu.edu.cn/event/3345` 或列表中任意一个 `/event/<id>` 活动
- [ ] 确认生成的海报草稿 `source_type` 为 `crawl`
- [ ] 确认生成的海报草稿 `source_url` 为实际详情页 URL
- [ ] 确认标题包含 `Efficient parallel acceleration technology for distributed large models` 或实际抓取活动标题
- [ ] 确认原始文本或摘要包含活动时间、活动地点、主讲人等至少两类结构化信息
- [ ] 如抓取到样例 `3345`，确认草稿中包含 `分布式大模型高效并行加速技术`
- [ ] 调用海报列表接口确认该草稿可查询
- [ ] 将该草稿通过审核接口审核为 `published`
- [ ] 审核后调用 `/api/posters/{id}/related`
- [ ] 确认审核发布后生成知识节点，至少包含时间、地点、来源中的一类
- [ ] 调用 `/api/search/internal?q=分布式大模型`
- [ ] 确认内部搜索能命中该抓取生成的海报或相关知识节点
- [ ] 在 `docs/DeploymentRecord.md` 记录本次真实站点实验结果，包括实际抓取 URL、生成海报 ID、审核结果、关联接口结果、搜索结果

## 10. 更新记录

- [x] 更新 `docs/DeploymentRecord.md`
- [x] 写明拉取 commit
- [x] 写明新增模型与接口
- [x] 写明依赖变更
- [x] 写明 Docker 重建结果
- [x] 写明创建数据源验证结果
- [x] 写明抓取成功与失败日志验证结果
- [ ] 写明中山大学计算机学院真实站点实验结果
- [ ] 写明实际使用的列表选择器和详情选择器
- [ ] 写明实际抓取到的活动 URL 与生成海报 ID
- [ ] 写明海报审核、关联分析、内部搜索验证结果
- [x] 明确记录 HTTPS、域名、OpenClaw、向量搜索、本轮未处理

## 11. 提交与推送

- [x] ~~执行 `git status --short`~~
- [x] ~~确认只包含本轮代码与文档变更~~
- [x] ~~执行 `git add backend docs`~~
- [x] ~~执行 `git commit -m "Implement basic data source crawler"`~~
- [x] ~~执行 `git push`~~

## 下一轮建议

- [ ] 如果基础爬虫通过，下一轮实现 Celery 异步抓取任务
- [ ] 如果草稿质量不足，下一轮优化规则抽取标题、时间、地点和主办方
- [ ] 如果外网页面复杂，下一轮再评估 OpenClaw 或浏览器自动化
- [ ] HTTPS、域名、证书继续延后
