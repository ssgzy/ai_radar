# 任务笔记 - AI Radar 搭建

关联：[[项目总览]] | [[当前状态]] | [[系统架构]] | [[模块说明]] | [[版本迭代记录]] | [[下一步]]

## 任务目标

从真实目录出发，构建一个可持续迭代、可追踪、可落地到 Obsidian 的 AI Radar 系统。当前重点已经从 V1 转到 V2：在原有闭环上加入评分、标签、排序和更强的运行记录。

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

本轮只承诺做 V1，不一次性铺满全部来源和全部 Agent；但结构会为 V2-V5 预留清晰接口。

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
