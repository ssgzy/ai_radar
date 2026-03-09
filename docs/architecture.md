# AI Radar 架构说明

当前版本已进入 V2，已经实现以下闭环：

1. 采集：`arXiv`、`GitHub`
2. 处理：本地 `Ollama` 中文总结
3. 分析：`Tagger`、`Scorer`
4. 导出：`processed JSON`、`scored JSON`、Obsidian 条目笔记、日报
5. 状态：`last_run`、`seen_*`、`source_checkpoints`、运行耗时和阶段统计

后续会按 V2-V5 继续加入评分、标签、更多来源、去重和自动化调度。
