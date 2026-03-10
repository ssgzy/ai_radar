# AI Radar 架构说明

当前版本已完成 V4，已经实现以下闭环：

1. 采集：`arXiv`、`GitHub`、`RSS`、`Hacker News`、`News`
2. 处理：本地 `Ollama` 中文总结
3. 分析：`Tagger`、`Scorer`、`Deduper`
4. 导出：`processed JSON`、`merged JSON`、`deduped JSON`、`duplicate report`、`failed_items`、Obsidian 条目笔记、日报、周报
5. 状态：`last_run`、`seen_*`、`source_checkpoints`、运行耗时、阶段统计、`runtime_context`

## 当前分层

### 数据采集层

- 统一通过 `collectors/` 输出 `RawItem`
- `BaseFeedCollector` 负责 RSS 类来源的共用抓取逻辑
- `HackerNewsCollector` 负责热门条目抓取和关键词过滤

### 内容处理层

- `LocalOllamaSummarizer` 负责中文总结
- `KeywordTagger` 负责标签
- `HeuristicScorer` 负责启发式评分
- `HeuristicDeduper` 负责跨来源去重

### 输出层

- 每个来源先写各自的 `raw/processed JSON`
- 全部合并后生成 `merged JSON`
- 去重后生成 `deduped JSON` 和 `duplicate report`
- 最终输出 Obsidian 条目笔记和日报

### 自动化层

- 当前可用入口是 `run_once.py`、`run_manual.py`、`run_ai_radar.py`
- `run_ai_radar.py` 默认作为 `scheduler` 入口
- `RuntimeTaskManager` 负责运行锁和 PID 元信息
- 已可生成 `cron / launchd` 示例配置

后续会按 V5 继续加入失败重试、陈旧锁恢复、更强的来源过滤、主题聚合和质量检查。
