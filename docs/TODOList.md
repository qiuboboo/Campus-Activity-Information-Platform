# TODO List: Backend Knowledge Graph Feature Round

本文是下一轮后端功能开发清单。目标是先按技术文档实现第一版“知识节点、海报关联、相关活动接口”，暂不处理 HTTPS、域名、前端页面和 OpenClaw。

默认约定：

- 本轮只做后端功能
- 优先保持现有 Flask 项目结构
- 优先兼容当前 PostgreSQL Docker 部署
- 不引入复杂迁移工具，当前阶段继续使用 `AUTO_CREATE_TABLES`
- 完成后更新 `docs/DeploymentRecord.md`

## 0. 拉取与检查

- [x] 执行 `git pull --ff-only`
- [x] 执行 `git status --short --branch`
- [x] 确认本地工作区干净
- [x] 执行 `python -m compileall backend` 或服务器等价命令
- [x] 记录当前起始 commit

## 1. 扩展数据库模型

- [x] 在 `backend/app/models.py` 中新增 `KnowledgeNode`
- [x] 在 `backend/app/models.py` 中新增 `PosterNode`
- [x] 在 `backend/app/models.py` 中新增 `PosterLink`
- [x] 为 `Poster` 增加到知识节点和海报关系的 relationship
- [x] 为新增模型实现 `to_dict()`
- [x] 保持字段命名与 `docs/后端技术文档.md` 中的设计一致

## 2. 实现知识节点生成服务

- [x] 新增或扩展服务层模块，用于从海报字段生成节点
- [x] 支持时间节点
- [x] 支持地点节点
- [x] 支持组织节点
- [x] 支持主题节点
- [x] 支持来源节点
- [x] 节点按 `name + node_type` 去重
- [x] 生成 `PosterNode` 关联关系

## 3. 实现海报关系建链

- [x] 实现同日关系 `same_day`
- [x] 实现同地点关系 `same_place`
- [x] 实现同主办方关系 `same_org`
- [x] 实现同主题关系 `same_topic`
- [x] 避免重复创建相同方向关系
- [x] 确认审核通过时自动触发关联生成
- [x] 确认更新海报后可重新生成关联

## 4. 实现关联信息接口

- [x] 新增 `GET /api/posters/{id}/related`
- [x] 返回当前海报基本信息
- [x] 返回直接关联知识节点
- [x] 返回共享节点的相关海报
- [x] 返回海报到海报的直接关系
- [x] 返回关联原因或关系类型
- [x] 保持返回结构便于前端展示

## 5. 实现知识节点查询接口

- [x] 新增知识节点 API 蓝图
- [x] 实现 `GET /api/knowledge/nodes`
- [x] 支持按 `node_type` 过滤
- [x] 支持按关键词搜索
- [x] 实现 `GET /api/knowledge/nodes/{id}`
- [x] 节点详情返回关联海报列表

## 6. 完善内部搜索

- [x] 新增搜索 API 蓝图
- [x] 实现 `GET /api/search/internal?q=...`
- [x] 搜索海报标题、摘要、原文
- [x] 搜索知识节点名称和描述
- [x] 返回命中类型 `poster` / `knowledge_node`
- [x] 暂不实现向量搜索，只实现关键词搜索

## 7. 准备演示数据

- [x] 更新 `seed-demo` 命令
- [x] 至少创建 3 条活动海报
- [x] 演示数据应包含共享地点
- [x] 演示数据应包含共享主办方
- [x] 演示数据应包含共享主题
- [x] 执行后可直接看到关联结果

## 8. 文档与接口示例

- [x] 新增 `docs/APIExamples.md`
- [x] 写登录示例
- [x] 写创建海报示例
- [x] 写审核通过示例
- [x] 写查看关联信息示例
- [x] 写知识节点查询示例
- [x] 写内部搜索示例

## 9. 本地验证

- [x] 执行 `python -m compileall backend`
- [ ] 如本地依赖可用，执行 Flask 启动验证（本机缺少 Flask 依赖，交由服务器验证）
- [ ] 验证登录接口（交由服务器 Docker 环境验证）
- [ ] 验证创建海报接口（交由服务器 Docker 环境验证）
- [ ] 验证审核接口（交由服务器 Docker 环境验证）
- [ ] 验证 `/api/posters/{id}/related`（交由服务器 Docker 环境验证）
- [ ] 验证 `/api/knowledge/nodes`（交由服务器 Docker 环境验证）
- [ ] 验证 `/api/search/internal`（交由服务器 Docker 环境验证）

## 10. 服务器验证

- [x] 服务器执行 `git pull --ff-only`
- [x] 重启后端容器
- [x] 执行健康检查 — **`{"status":"ok"}`**
- [x] 执行登录接口 — **返回 JWT token**
- [x] 执行演示数据生成 — **3 条海报 + 12 个知识节点**
- [x] 验证关联信息接口 — **Poster 1 关联 Poster 2 (同日/同地)、Poster 3 (同主办方)**
- [x] 验证知识节点接口 — **12 个节点，支持按 type 过滤**
- [x] 验证内部搜索接口 — **搜索"校园"返回 2 条海报结果**

> 额外修复：`db.create_all()` 在 Gunicorn 多 Worker 下的并发冲突。通过将建表逻辑移到 `on_starting` hook + `preload_app=True` 解决。

## 11. 记录与提交

- [x] 更新 `docs/DeploymentRecord.md`
- [x] 写明本轮实现范围
- [x] 写明本轮未做 HTTPS、域名、OpenClaw、向量搜索
- [x] 写明接口验证结果
- [x] ~~执行 `git status --short`~~
- [x] ~~提交代码与文档~~
- [x] ~~推送到 GitHub~~

## 下一轮建议

- [ ] 如果本轮成功，下一轮实现数据源与基础爬虫
- [ ] 如果关联接口不稳定，下一轮聚焦关系生成规则和测试数据
- [ ] HTTPS、域名、证书继续延后
