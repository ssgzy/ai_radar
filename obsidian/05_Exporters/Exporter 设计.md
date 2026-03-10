# Exporter 设计

关联：[[系统架构]] | [[数据说明]] | [[结果索引]] | [[模块说明]]

## 当前已实现

- `JsonExporter`
- `ObsidianExporter`
- `DebugExporter`
- `ReportExporter`

## 当前输出

- 原始 JSON：`data/raw/<source>/<YYYY-MM-DD>/`
- 处理后 JSON：`data/processed/<source>/<YYYY-MM-DD>/`
- merged JSON：`data/processed/merged/<YYYY-MM-DD>/`
- deduped JSON：`data/processed/deduped/<YYYY-MM-DD>/`
- duplicate report：`data/processed/deduped/<YYYY-MM-DD>/`
- scored JSON：`data/processed/scored/<YYYY-MM-DD>/`
- failed_items：`outputs/debug/failed_items/<YYYY-MM-DD>/`
- Obsidian 条目笔记：
  - `outputs/obsidian/papers/`
  - `outputs/obsidian/projects/`
  - `outputs/obsidian/inbox/`
- Obsidian 日报：
  - `outputs/obsidian/dashboards/daily/<YYYY-MM-DD>/`
- Obsidian 周报：
  - `outputs/obsidian/dashboards/weekly/<YYYY-Www>/`
- reports 周报副本：
  - `outputs/reports/weekly/<YYYY-Www>/`

## 当前设计选择

- 条目笔记和日报都建立 `[[Wikilinks]]`
- 输出路径尽量稳定，便于长期沉淀
- 调试信息单独放到 `outputs/debug/`
- 日报按分数排序
- 条目笔记显示推荐级别、分数拆解和标签
- 日报展示去重前后数量、重复移除数和每来源去重后统计
- 周报聚合最近 7 天运行日志
- 历史搜索结果按天归档，避免根目录越堆越乱
