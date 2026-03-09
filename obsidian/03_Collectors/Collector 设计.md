# Collector 设计

关联：[[系统架构]] | [[模块说明]] | [[数据说明]] | [[下一步]]

## V1 已实现

- `ArxivCollector`
- `GitHubCollector`

## 当前接口

- 统一继承 `BaseCollector`
- 统一输出 `RawItem`
- 每个 collector 自己负责：
  - 来源查询参数
  - 原始字段清洗
  - 采集阶段进度输出

## 当前设计选择

- `arXiv` 保留完整摘要，不做强行截断
- `GitHub` 在仓库描述为空时，补充仓库名、语言和 Stars，避免下游总结信息不足

## 后续扩展

- `RSSCollector`
- `HackerNewsCollector`
- `NewsCollector`
- `RedditCollector`
- `ProductHuntCollector`
