# Exporter 设计

关联：[[系统架构]] | [[数据说明]] | [[结果索引]] | [[模块说明]]

## 当前已实现

- `JsonExporter`
- `ObsidianExporter`

## 当前输出

- 原始 JSON：`data/raw/<source>/`
- 处理后 JSON：`data/processed/<source>/`
- merged JSON：`data/processed/merged/`
- scored JSON：`data/processed/scored/`
- Obsidian 条目笔记：
  - `outputs/obsidian/papers/`
  - `outputs/obsidian/projects/`
- Obsidian 日报：
  - `outputs/obsidian/dashboards/`

## 当前设计选择

- 条目笔记和日报都建立 `[[Wikilinks]]`
- 输出路径尽量稳定，便于长期沉淀
- 调试信息单独放到 `outputs/debug/`
- 日报按分数排序
- 条目笔记显示推荐级别、分数拆解和标签
