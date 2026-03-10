# 任务笔记 - AI Radar 搭建

关联：[[项目总览]] | [[当前状态]] | [[系统架构]] | [[模块说明]] | [[版本迭代记录]] | [[下一步]]

## 任务目标

从真实目录出发，构建一个可持续迭代、可追踪、可落地到 Obsidian 的 AI Radar 系统。当前重点已经推进到 V3：在原有 `arXiv + GitHub + Ollama + scoring/tags` 闭环上，继续接入更多来源并加入正式的 merge / dedupe。

## 本轮约束

- 不假设继承旧项目上下文
- 所有说明性 Markdown 默认中文
- 重要动作必须同步写入 Obsidian
- 任何 Python 文件都要包含中文注释和中文 docstring
- 运行时不能长时间无输出

## 本轮执行计划

1. 核查现有目录和代码
2. 初始化项目目录和 Obsidian 笔记
3. 设计 V1 分层结构
4. 重构 collector / summarizer / exporter / pipeline / CLI
5. 做一次真实运行并记录结果
6. 更新 [[版本迭代记录]]、[[结果索引]]、[[问题与坑点]]

## 目前观察

- 已有一个非常早期的最小脚本版本
- 原始抓取结果已经产生过几份，但输出目录尚未分层
- 现有代码可以帮助确认 API 可达思路，但不适合直接扩展成正式结构

## 当前任务边界

当前阶段已经完成 V1-V3 的连续迭代；后续不再回到“大一统脚本”做法，而是继续按版本推进。

## 本轮已完成

- 完成项目目录和 Obsidian 中文知识库初始化
- 完成 `arXiv` 与 `GitHub` collector 重构
- 完成本地 Ollama 总结器封装和模型回退策略
- 完成 JSON 导出、Obsidian 条目笔记导出、日报导出
- 完成运行状态落盘：`last_run`、`seen_ids`、`seen_urls`、`seen_titles`、`source_checkpoints`
- 完成运行心跳提示，避免模型等待像假死
- 完成 2 个基础测试并通过

## 关键文件改动

### 新增 / 重写的关键入口

- `README.md`
- `pyproject.toml`
- `requirements.txt`
- `run_once.py`
- `run_manual.py`
- `run_ai_radar.py`

### 新增 / 重写的关键配置

- `config/settings.py`
- `config/sources.yaml`
- `config/models.yaml`
- `config/prompts.yaml`
- `config/obsidian.yaml`
- `config/scoring.yaml`

### 新增 / 重写的关键代码

- `src/pipeline.py`
- `src/cli.py`
- `src/main.py`
- `src/collectors/base_collector.py`
- `src/collectors/arxiv_collector.py`
- `src/collectors/github_collector.py`
- `src/agents/summarizer.py`
- `src/exporters/json_exporter.py`
- `src/exporters/obsidian_exporter.py`
- `src/models/raw_item.py`
- `src/models/processed_item.py`
- `src/models/source_record.py`
- `src/utils/ollama_client.py`
- `src/utils/logger.py`
- `src/utils/file_ops.py`
- `src/utils/text_utils.py`
- `src/utils/obsidian_utils.py`
- `src/utils/markdown_utils.py`

### 新增测试与辅助脚本

- `scripts/test_ollama.py`
- `tests/test_summarizer.py`
- `tests/test_pipeline.py`

## 实际运行命令

```bash
python -m compileall config src scripts tests run_once.py run_manual.py run_ai_radar.py
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/test_ollama.py
python run_once.py --max-items 1
python run_once.py --max-items 1
```

## 实际产出

- 基线运行 ID：`20260310_021607`
- 合并结果：`data/processed/merged/merged_20260310_021607.json`
- 日报：`outputs/obsidian/dashboards/AI Radar 日报 - 2026-03-10 - 20260310_021607.md`
- 条目笔记：
  - `outputs/obsidian/papers/论文 - Multimodal Large Language Models as Image Classifiers.md`
  - `outputs/obsidian/projects/项目 - OpenLoaf OpenLoaf.md`

## 当前结论

- V1 已达到“可运行、可追踪、可沉淀”的最低可用标准
- 当前代码结构已经为 V2 的评分、标签、更多来源和自动化预留出清晰接口
- `mistral:7b` 更适合作为当前机器上的默认模型，`qwen3.5:9b` 仍保留为可切换选项

## V2 本轮计划

1. 给 `ProcessedItem` 增加结构化评分、分项得分、标签和推荐级别
2. 新增 `Scorer` 与 `Tagger` 模块
3. 改进 Obsidian 日报和条目笔记：
   - 按总分排序
   - 显示推荐级别
   - 显示分数拆解
   - 显示标签
4. 增强运行记录：
   - 总耗时
   - 每个来源耗时
   - 每个阶段统计
5. 真实运行一次 V2，并写入 [[版本迭代记录]]

## V2 本轮已完成

- 已新增 `Scorer` 与 `Tagger`
- 已让 `ProcessedItem` 携带结构化分数、标签和推荐级别
- 已新增 `scored JSON`
- 已让日报按总分排序
- 已让条目笔记显示推荐级别、总分、分数拆解、标签和关注建议
- 已让运行状态记录包含总耗时、每个来源耗时和每阶段统计

## V2 实际运行命令

```bash
python -m compileall config src tests run_once.py run_manual.py run_ai_radar.py
python -m pytest -q
python run_once.py --max-items 2
```

## V2 实际产出

- 运行 ID：`20260310_024851`
- 合并结果：`data/processed/merged/merged_20260310_024851.json`
- 评分结果：`data/processed/scored/scored_20260310_024851.json`
- 日报：`outputs/obsidian/dashboards/AI Radar 日报 - 2026-03-10 - 20260310_024851.md`
- 重点条目：
  - `Multimodal Large Language Models as Image Classifiers`
  - `Omni-Diffusion: Unified Multimodal Understanding and Generation with Masked Discrete Diffusion`
  - `ed-donner/llm_engineering`

## V2 当前结论

- V2 已达到“可打分、可排序、可标签化”的标准
- 当前评分是启发式规则版本，已经适合做第一轮筛选，但还不是最终版智能排序
- V3 应转向多源扩展与 merge / dedupe

## V3 本轮计划

1. 新增 `RSSCollector`
2. 新增 `HackerNewsCollector`
3. 新增 `NewsCollector`
4. 在 `config/sources.yaml` 中加入真实默认源
5. 实现 merge / dedupe，产出 deduped JSON
6. 用真实多源数据跑一次 V3，并写入 [[版本迭代记录]]

## V3 本轮已完成

- 已新增 `BaseFeedCollector`
- 已新增 `RSSCollector`
- 已新增 `HackerNewsCollector`
- 已新增 `NewsCollector`
- 已新增 `HeuristicDeduper`
- 已让 `pipeline` 在合并后执行 `dedupe`
- 已新增 `deduped JSON` 与 `duplicate report`
- 已让 `ObsidianExporter` 为 `rss / hackernews / news` 输出 `inbox` 笔记
- 已让日报展示去重前后数量、重复移除数和每个来源的去重后条目数
- 已修正 `Hacker News` 短关键词的误判问题
- 已修正 `deduped/scored JSON` 的 `note_path` 回写时序问题

## V3 实际运行命令

```bash
python -m pytest -q
python run_once.py --max-items 1
python run_once.py --max-items 1
python run_once.py --max-items 1
```

## V3 实际产出

- 运行 ID：`20260310_032532`
- 合并结果：`data/processed/merged/merged_20260310_032532.json`
- 去重结果：`data/processed/deduped/deduped_20260310_032532.json`
- 重复报告：`data/processed/deduped/duplicates_20260310_032532.json`
- 评分结果：`data/processed/scored/scored_20260310_032532.json`
- 日报：`outputs/obsidian/dashboards/AI Radar 日报 - 2026-03-10 - 20260310_032532.md`
- 条目笔记：
  - `outputs/obsidian/papers/论文 - Multimodal Large Language Models as Image Classifiers.md`
  - `outputs/obsidian/projects/项目 - Aiddrag83 Aiden-Piercey---COMP1054WINTER2026.md`
  - `outputs/obsidian/inbox/资讯 - Granite 4.0 1B Speech Compact, Multilingual, and Built for the Edge.md`
  - `outputs/obsidian/inbox/资讯 - AI Didn't Break the Senior Engineer Pipeline. It Showed That One Never Existed.md`
  - `outputs/obsidian/inbox/资讯 - OpenAI acquires Promptfoo to secure its AI agents.md`

## V3 当前结论

- V3 已达到“多源采集 + 去重导出 + 资讯统一落 inbox”的阶段目标
- 真实数据源已经从 `arXiv / GitHub` 扩展到 `RSS / Hacker News / News`
- 当前去重为启发式首版，已经能支撑 V3，但后续仍需更强的标题语义和 URL 归一化策略
- 最新基线样本里重复数为 `0`，说明本次数据集没有撞到明显重复；这不代表 dedupe 可以省略
- 收尾复测已完成：`python -m pytest -q`，结果 `6 passed`

## V4 预备计划

1. 增加 `failed_items` 调试输出
2. 细化 `run_once / manual / scheduler` 的职责边界
3. 开始落实 `cron / launchd` 预留方案
4. 增加 `daily / weekly brief` 的自动化文档和脚本

## V4 本轮计划

1. 为 `summarizer / exporter / source` 失败增加结构化记录
2. 增加 `scheduler` 模式的运行锁和 PID 元信息
3. 新增 `cron / launchd` 配置生成模块和脚本
4. 自动生成周报并写入 Obsidian
5. 做真实运行并更新 [[版本迭代记录]]

## V4 本轮已完成

- 已新增 `FailedItemRecord`
- 已新增 `DebugExporter`
- 已新增 `ReportExporter`
- 已新增 `RuntimeTaskManager`
- 已新增 `cron_runner / launchd_runner`
- 已让 `summarizer` 在单条失败时继续处理后续条目
- 已让 `pipeline` 输出 `failed_items_path`、`weekly_brief_path`、`weekly_report_path`
- 已让 `run_ai_radar.py` 作为默认 scheduler 入口
- 已新增 `scripts/run_scheduler_once.sh`
- 已新增 `scripts/generate_scheduler_assets.py`
- 已让周报自动聚合最近 7 天运行日志

## V4 实际运行命令

```bash
python -m compileall src scripts run_ai_radar.py run_manual.py run_once.py
python -m pytest -q
python scripts/generate_scheduler_assets.py --hour 9 --minute 0
python run_ai_radar.py --max-items 1
```

## V4 实际产出

- 运行 ID：`20260310_035123`
- 合并结果：`data/processed/merged/merged_20260310_035123.json`
- 去重结果：`data/processed/deduped/deduped_20260310_035123.json`
- 重复报告：`data/processed/deduped/duplicates_20260310_035123.json`
- 评分结果：`data/processed/scored/scored_20260310_035123.json`
- 日报：`outputs/obsidian/dashboards/AI Radar 日报 - 2026-03-10 - 20260310_035123.md`
- 周报：`outputs/obsidian/dashboards/AI Radar 周报 - 2026-W11.md`
- 周报副本：`outputs/reports/weekly/AI Radar 周报 - 2026-W11.md`
- 失败记录：`outputs/debug/failed_items/failed_items_20260310_035123.json`
- 调度示例：
  - `outputs/exports/markdown/scheduling/cron.example.txt`
  - `outputs/exports/markdown/scheduling/ai_radar.launchd.plist`

## V4 当前结论

- V4 已达到“手动 / 单次 / 调度区分明确、失败可追踪、周报可自动生成”的阶段目标
- 当前 scheduler 模式已经具备陈旧锁自动恢复，并已通过真实验证
- `failed_items` 不仅会落盘，还已经通过真实失败样本回放恢复成功
- `Hacker News` 已从简单关键词匹配升级为强/弱信号评分；当前命中项属于 AI 工程相关条目，而不是误判
- `run_id` 同秒碰撞问题已修复为微秒级时间戳
- V4 最终回归已通过：`python -m pytest -q`，结果 `16 passed`

## V4 补充验证命令

```bash
python run_ai_radar.py --sources rss --max-items 1
OLLAMA_HOST=http://127.0.0.1:9 python run_manual.py --sources rss --max-items 1
python scripts/retry_failed_items.py --failed-file outputs/debug/failed_items/failed_items_20260310_040621.json --max-items 1
python run_ai_radar.py --max-items 1
python -m pytest -q
```

## 仓库整理与归档

### 本轮目标

- 把真正没用或命名混乱的测试类文件归档起来
- 把每天的搜索结果改成按日期归档
- 把每周的周报改成按周目录归档
- 清理仓库里的缓存和早期平铺产物

### 本轮决策

- 保留 `tests/`：这些是正式自动化测试，不归档
- 归档 `scripts/test_ollama.py`：它是早期的测试命名脚本，当前入口改为 `scripts/healthcheck_ollama.py`
- 归档早期平铺 raw JSON：放入 `archive/legacy/raw_flat/`
- 历史运行产物不删除，迁移到更清晰的日期/周目录

### 本轮实际执行命令

```bash
python -m compileall src scripts run_ai_radar.py run_manual.py run_once.py
python -m pytest -q
python scripts/healthcheck_ollama.py
python run_once.py --max-items 1
```

### 本轮实际产出

- 最新运行 ID：`20260310_042523_551180`
- 最新合并结果：`data/processed/merged/2026-03-10/merged_20260310_042523_551180.json`
- 最新去重结果：`data/processed/deduped/2026-03-10/deduped_20260310_042523_551180.json`
- 最新评分结果：`data/processed/scored/2026-03-10/scored_20260310_042523_551180.json`
- 最新日报：`outputs/obsidian/dashboards/daily/2026-03-10/AI Radar 日报 - 2026-03-10 - 20260310_042523_551180.md`
- 当前周报：`outputs/obsidian/dashboards/weekly/2026-W11/AI Radar 周报 - 2026-W11.md`
- 当前周报副本：`outputs/reports/weekly/2026-W11/AI Radar 周报 - 2026-W11.md`
- 最新失败记录：`outputs/debug/failed_items/2026-03-10/failed_items_20260310_042523_551180.json`
- 最新运行日志：`logs/runs/2026-03-10/20260310_042523_551180.json`
- 归档脚本：`archive/scripts/test_ollama.py`
- 归档平铺数据：`archive/legacy/raw_flat/`

### 本轮结论

- 仓库已经从“结果平铺”整理成“按天/按周归档”
- 新结构不只迁移了旧文件，也已经通过真实运行验证
- 以后找某天结果，可以直接去对应日期目录，不需要在根目录翻一长串文件
