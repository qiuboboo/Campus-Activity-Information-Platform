# 异步任务设计

Celery 主要承担以下任务：

- 抓取外部网页
- 调用 LLM 执行智能提取与分析
- 生成海报 Embedding
- 生成知识节点 Embedding
- 批量更新关联关系
- 定时清洗失效来源

## 队列划分

- `crawl`：抓取任务
- `ai`：LLM 与语义分析任务
- `index`：向量生成与索引维护任务（`build_poster_embedding`、`build_node_embedding`、`rebuild_all_embeddings`）

## 设计原则

- 接口层只负责提交任务，不直接执行耗时逻辑
- 所有任务记录执行日志，便于排错和展示
- 对外部调用设置超时和重试上限
