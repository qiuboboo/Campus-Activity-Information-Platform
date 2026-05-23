# 搜索页前端设计文档（仅内部搜索）

## 1. 设计目标

搜索页只承担平台内部检索职责：在已入库的活动海报和知识节点中查找相关内容。当前版本不设计、不展示、不联调外部搜索能力。

核心目标：

- 搜索入口统一指向内部搜索接口：`GET /api/search/internal?q=<keyword>`。
- 主页搜索框默认跳转 `/search?q=<keyword>`，搜索页自动回填关键词并执行内部搜索。
- 搜索结果只包含两类：活动海报 `poster`、知识节点 `knowledge_node`。
- 结果点击沿用现有详情路由：海报 `/posters/:id`，知识节点 `/knowledge/:id`。
- 页面不出现“外部搜索”“LLM”“平台外线索”“mode=external”等概念。

## 2. 后端接口契约

### 2.1 认证要求

接口受 JWT 保护：

- 未登录访问 `/search` 会被前端路由守卫跳转到 `/auth/login`。
- 未携带 token 调用接口时，后端返回 `401`。
- 页面不需要单独处理登录跳转，保持现有 API client 和路由守卫逻辑即可。

### 2.2 内部搜索接口

接口：

```http
GET /api/search/internal?q=<keyword>
```

正常返回：

```json
{
  "items": [
    {
      "hit_type": "poster",
      "item": {}
    },
    {
      "hit_type": "knowledge_node",
      "item": {}
    }
  ],
  "query": "讲座",
  "search_mode": "fulltext"
}
```

空查询返回：

```json
{
  "items": [],
  "query": ""
}
```

实现特征：

- 后端会对 `q` 执行 `trim()`。
- 当前接口只读取 `q`，没有分页、排序、分类筛选参数。
- 海报搜索字段：`title`、`summary`、`raw_text`、`location`、`organizer`。
- 知识节点搜索字段：`name`、`description`。
- 海报最多返回 20 条，知识节点最多返回 20 条。
- `EMBEDDING_ENABLED=true` 时，海报优先走向量检索并补充 LIKE 命中；知识节点仍走 LIKE。
- `search_mode` 为 `vector` 或 `fulltext`；空查询时可能缺失。

## 3. 页面信息架构

页面分为 4 个区域。

### 3.1 顶部说明区

内容：

- 页面标题：`搜索`
- 副标题：`在平台活动库和知识节点中查找校园活动信息`
- 辅助说明：当前搜索范围为“活动海报 + 知识节点”。

设计要求：

- 页面位于现有 `AppLayout` 内，不重复实现主页导航栏。
- 视觉风格和后台功能页保持一致，搜索区域比普通表单更突出。

### 3.2 搜索操作区

组件元素：

- 关键词输入框。
- 主按钮：`搜索`。
- 可选建议关键词：`讲座`、`竞赛`、`志愿服务`、`科技节` 等。

交互规则：

- 输入为空时不发起请求。
- 支持回车搜索。
- 支持清空输入。
- 请求期间禁用重复提交，按钮显示 loading。
- 搜索后同步路由：`/search?q=<keyword>`。
- 不设计内部/外部 Tab，不设计 `mode` 参数。

### 3.3 结果摘要区

展示内容：

- 当前关键词：使用后端返回的 `query`。
- 命中数量：`items.length`。
- 搜索模式：使用后端返回的 `search_mode`。

模式文案映射：

| `search_mode` | 前端文案 |
|---------------|----------|
| `vector` | 语义向量 |
| `fulltext` | 全文检索 |
| 缺失 | 未执行搜索 |

展示示例：

```text
关键词“讲座”：共 6 条结果 · 全文检索
```

### 3.4 结果列表区

结果只处理两种 `hit_type`。

海报卡片：

- 标题：`item.title`。
- 摘要：`item.summary`，最多展示 2 到 3 行。
- 元信息：`event_time`、`location`、`organizer`、`activity_type`。
- 状态标签：`draft`、`pending_review`、`published`、`rejected`。
- 点击跳转：`/posters/:id`。

知识节点卡片：

- 标题：`item.name`。
- 类型：`item.node_type`。
- 别名：`item.alias`，存在时显示。
- 描述：`item.description`。
- 来源链接：`item.source_url`，存在时作为次级信息展示。
- 点击跳转：`/knowledge/:id`。

排序规则：

- 前端保持后端返回顺序，不在前端二次排序。
- 当前后端顺序为：海报结果在前，知识节点结果在后。

## 4. 状态设计

### 4.1 初始态

触发条件：没有路由 `q`，且用户尚未搜索。

展示内容：

- 简短说明：搜索会覆盖活动标题、摘要、正文、地点、组织者，以及知识节点名称和描述。
- 建议关键词按钮，点击后填入关键词并触发搜索。

### 4.2 加载态

展示要求：

- 搜索按钮 loading。
- 结果区显示加载态或骨架屏。
- 新请求开始时清空旧结果，避免用户误认为旧结果属于新关键词。

### 4.3 空结果态

触发条件：搜索完成且 `items.length === 0`。

展示文案：

```text
未在平台活动库和知识节点中找到相关内容
```

辅助建议：

- 换一个更宽泛的关键词。
- 尝试搜索活动地点、组织者或主题词。

### 4.4 请求异常态

触发条件：HTTP `401`、`500`、网络超时等。

处理方式：

- `401` 交给统一 client/路由登录逻辑。
- `500` 或网络异常显示：`搜索请求失败，请稍后重试`。
- 清空当前结果，避免展示过期结果。

## 5. 路由与页面初始化

进入页面时只读取：

- `route.query.q`

初始化规则：

- `q` 存在时，回填输入框并自动执行内部搜索。
- `q` 不存在时，展示初始引导态。
- 不读取、不写入 `mode`。

搜索后更新路由：

```ts
router.replace({
  path: '/search',
  query: { q: keyword.value.trim() },
})
```

注意：避免 `router.replace` 与监听 `route.query.q` 互相触发造成重复请求。建议用一个内部标记区分“用户主动搜索”和“路由变化触发搜索”。

## 6. 主页搜索入口约定

主页搜索框行为：

- 用户输入关键词后，跳转 `/search?q=<keyword>`。
- 搜索页收到 `q` 后自动执行内部搜索。
- 主页不需要传 `mode`，也不需要展示内部/外部选择。

示例：

```ts
router.push({ path: '/search', query: { q } })
```

该行为已经符合“默认指向内部搜索”的要求，搜索页实现时必须保持这一默认语义。

## 7. 前端数据类型建议

建议在 `frontend/src/api/search.ts` 中补充类型，减少页面中的 `any`。

```ts
export type SearchMode = 'fulltext' | 'vector'
export type SearchHitType = 'poster' | 'knowledge_node'

export interface InternalSearchHit<T = unknown> {
  hit_type: SearchHitType
  item: T
}

export interface InternalSearchResponse {
  items: InternalSearchHit[]
  query: string
  search_mode?: SearchMode
}

export function internalSearch(q: string) {
  return client.get<InternalSearchResponse>('/search/internal', { params: { q } })
}
```

页面不需要引入 `externalSearch`。如果 API 文件中保留 `externalSearch`，搜索页也不应使用它。

## 8. 当前代码差距

### 8.1 `SearchView.vue`

当前问题：

- 页面仍有“内部搜索 / 外部搜索”Tab，需要删除。
- 页面仍会调用 `externalSearch`，需要移除。
- 没有读取路由 `q`，主页搜索跳转后不会自动搜索。
- 搜索结果类型使用 `any[]`，建议改为内部搜索响应类型。
- `search_mode` 展示逻辑需要只服务内部搜索。
- 大量 inline style，不利于维护，建议改为 scoped class。

### 8.2 `frontend/src/api/search.ts`

当前建议：

- 保留 `internalSearch(q)`。
- 给 `internalSearch` 增加返回类型。
- `externalSearch(q)` 可暂时保留给未来功能，但搜索页不要导入或调用。

### 8.3 `frontend/mock-server.js`

当前问题：

- 缺少真实接口 `/api/search/internal`。
- 仍保留旧接口 `/api/search`，与搜索页 API 不一致。

重构要求：

- 增加 `GET /api/search/internal` mock。
- mock 返回结构必须是 `{ items, query, search_mode }`。
- 可保留 `GET /api/search` 作为旧兼容，但搜索页不得依赖它。
- 不需要为搜索页维护 `/api/search/external` mock。

## 9. 视觉规范

整体方向：清晰、轻量、可扫描，服务内部检索效率。

建议：

- 外层采用单列内容区，最大宽度约 `1080px`。
- 搜索操作区使用白色卡片，搜索框占据主视觉焦点。
- 结果卡片通过标签区分 `活动` 与 `知识节点`。
- 主按钮保持 Element Plus primary。
- 卡片 hover 只做轻微阴影和边框变化。
- 移动端搜索框和按钮纵向排列，结果卡片元信息自动换行。

## 10. 可访问性要求

- 搜索输入框设置明确 placeholder 与 `aria-label`。
- 搜索按钮可通过键盘触发。
- 结果卡片如果可点击，需要支持 `Enter` 触发跳转。
- 空状态和错误状态用文本表达，不只依赖颜色或图标。

## 11. 验收场景

必须覆盖：

- 访问 `/search`，展示初始引导态，不自动请求。
- 访问 `/search?q=讲座`，自动执行内部搜索。
- 主页输入关键词后跳转 `/search?q=<keyword>`，搜索页自动展示内部搜索结果。
- 输入关键词并点击搜索后，路由更新为 `/search?q=<keyword>`。
- 内部搜索有海报结果，点击跳转 `/posters/:id`。
- 内部搜索有知识节点结果，点击跳转 `/knowledge/:id`。
- 内部搜索空结果，显示内部空状态。
- 搜索接口异常时显示错误态并清空旧结果。
- mock-server 的 `/api/search/internal` 与真实后端字段一致。
- 页面中不出现外部搜索入口、外部搜索文案或外部搜索结果卡片。

## 12. 实施 TODO

- [ ] 1. 从 `SearchView.vue` 删除外部搜索 Tab、状态和 API 调用。
- [ ] 2. 为 `frontend/src/api/search.ts` 的 `internalSearch` 补充响应类型。
- [ ] 3. 增加路由 `q` 初始化、回填和自动内部搜索。
- [ ] 4. 搜索后同步路由为 `/search?q=<keyword>`。
- [ ] 5. 重写结果摘要区，准确显示 `query/items.length/search_mode`。
- [ ] 6. 重写两类结果卡片：活动海报、知识节点。
- [ ] 7. 移除主要 inline style，改为 scoped class。
- [ ] 8. 修正 `frontend/mock-server.js`，增加 `/api/search/internal` mock。
- [ ] 9. 检查 `HomeView.vue` 搜索跳转保持 `/search?q=<keyword>`，不传任何模式参数。
- [ ] 10. 更新前端本地测试指南中的搜索页说明（实现完成后）。
