# Collector 设计

关联：[[系统架构]] | [[模块说明]] | [[数据说明]] | [[下一步]]

## 当前已实现

- `ArxivCollector`
- `GitHubCollector`
- `BaseFeedCollector`
- `RSSCollector`
- `HackerNewsCollector`
- `NewsCollector`

## 当前接口

- 统一继承 `BaseCollector`
- 统一输出 `RawItem`
- 每个 collector 自己负责：
  - 来源查询参数
  - 原始字段清洗
  - 采集阶段进度输出

## V3 设计补充

- `BaseFeedCollector` 统一处理 `feedparser + requests` 的抓取逻辑
- RSS 类来源使用稳定的哈希 ID，避免原始链接过长或包含特殊字符
- `HackerNewsCollector` 先扫 `topstories`，再用关键词做轻量过滤
- `Hacker News` 的短关键词采用单词边界匹配，避免 `ai` 误命中普通单词片段
- `Hacker News` 当前还会计算强/弱信号相关性分数，并支持排除词

## 当前设计选择

- `arXiv` 保留完整摘要，不做强行截断
- `GitHub` 在仓库描述为空时，补充仓库名、语言和 Stars，避免下游总结信息不足

## 后续扩展

- `RedditCollector`
- `ProductHuntCollector`
