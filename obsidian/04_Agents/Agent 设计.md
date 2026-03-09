# Agent 设计

关联：[[系统架构]] | [[Prompt 设计]] | [[问题与坑点]] | [[下一步]]

## 当前已实现

- `LocalOllamaSummarizer`
- `KeywordTagger`
- `HeuristicScorer`

## 当前职责

- 组装 prompt
- 调用本地 Ollama
- 在等待时输出心跳提示
- 解析固定标题结果
- 清理 Markdown 噪音
- 生成 `ProcessedItem`
- 保留 prompt / response 调试文件
- 根据关键词规则生成标签
- 根据启发式规则生成分数和推荐级别

## V2 预留

- `Deduper`
- `BriefWriter`

## 当前取舍

- 默认模型先用 `mistral:7b`
- `qwen3.5:9b` 保留为可切换模型，不作为当前机器上的默认值
- 当前评分先用启发式规则，优先保证可解释和稳定
