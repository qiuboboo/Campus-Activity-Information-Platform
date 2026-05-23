# TODOList: 搜狗微信搜索集成

> **方案**：参考 weixin_search_mcp —— requests + lxml 抓取搜狗微信搜索
> **crawl_mode**：新增 `weixin` 模式

## 实施计划

- [x] `data_source_service.py` — validation 新增 `weixin` 模式
- [x] `weixin_search_service.py`（新建）搜狗微信搜索：
  - `sogou_search(query, page)` — 请求搜狗搜索，解析结果列表
  - `sogou_search_all(query, max_pages)` — 自动翻页
  - `_is_antispider(response)` — 反爬检测
  - `_convert_time(ts_str)` — 搜狗时间戳转 ISO 时间
  - `resolve_real_url(sogou_url)` — 从搜狗跳转链接提取真实文章 URL（支持 Cookie 绕过反爬）
  - `fetch_article_content(real_url)` — 从 `#js_content` 提取正文
  - `search_and_fetch(query)` — 一站式搜索→解析→抓取
- [x] `data_sources.py` — crawl 路由支持 weixin 模式，创建 Poster 草稿
- [x] `config.py` / `backend/.env` — 新增 `SOGOU_COOKIES` 配置项
- [ ] 测试 — 写单元测试 mock 搜狗搜索
- [x] 文档 — 更新数据源模块说明、后端技术文档

---

# Multi-Engine Search Integration (2026-05-24)

> **方案**：SearXNG（自托管元搜索引擎）+ 已有搜狗搜索
> **覆盖的引擎**：Google、Bing、DuckDuckGo、百度（通过 SearXNG）+ 搜狗微信（`weixin_search_service.py`）

## 实施计划

- [x] `deploy/searxng/settings.yml` — SearXNG 配置文件（限用 4 个引擎 + JSON 格式支持）
- [x] Docker — 启动 SearXNG 容器，接入 `backend_default` 网络
- [x] `multi_search_service.py`（新建）— 多引擎搜索服务：
  - `_search_searxng(query, engines)` — 调用 SearXNG JSON API
  - `_normalise_result(raw)` — SearXNG 结果转标准格式
  - `_normalise_sogou_result(raw)` — 搜狗结果转标准格式
  - `_deduplicate(results)` — 按 URL 去重
  - `search(query, engines)` — 聚合入口
- [x] `ai_service.search_external()` — 改为先走多引擎搜索，可选 LLM 兜底
- [x] `search.py` — `source` 字段改为 `"multi"`，支持 `sources` 参数
- [x] `config.py` / `backend/.env` — 新增 `SEARXNG_BASE_URL`
- [x] `search-contract.md` — 更新至 v2.0（多引擎 source 语义、新 error 取值）
- [x] `后端技术文档.md` — 更新外部搜索定义、搜索流程、接入优先级
- [ ] 测试 — 多引擎搜索单元测试 + 集成测试
- [ ] 部署文档 — 补充 SearXNG 容器管理说明

### 影响

| 变更 | 说明 |
|------|------|
| `source` 响应字段 | `"llm"` → `"multi"`（每条结果的 `source` 为具体引擎名） |
| 搜索结果来源 | LLM 幻觉 → 真实搜索引擎结果 |
| 新增依赖 | SearXNG Docker 容器（端口 8080 内部） |

### 变更记录

- 2026-05-23：新增 `SOGOU_COOKIES` 配置，`resolve_real_url` 支持 Cookie 绕过搜狗反爬，成功拿到 `mp.weixin.qq.com` 真实 URL。正文抓取仍受微信风控限制。
- 2026-05-23：原计划写在 `crawler_service.py`，后改为独立文件 `weixin_search_service.py`。
- 2026-05-24：Issue #8 — search_external 返回结构增加 error 字段；Issue #5 — 创建 docs/search-contract.md 搜索接口契约文档。
- 2026-05-24：多搜索引擎集成 — 新增 SearXNG 容器（Google/Bing/DuckDuckGo/百度）+ 已有搜狗搜索，外部搜索返回真实搜索结果；`search-contract.md` 更新至 v2.0；`source` 字段改为 `multi`。
