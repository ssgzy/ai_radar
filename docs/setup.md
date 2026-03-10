# 安装与运行

## 安装依赖

```bash
python -m pip install -r requirements.txt
```

## 检查 Ollama

```bash
python scripts/healthcheck_ollama.py
```

## 运行一次

```bash
python run_once.py --max-items 2
```

## 手动调试

```bash
python run_manual.py --sources arxiv github rss hackernews news --max-items 1
```

## scheduler 模式

```bash
python run_ai_radar.py --max-items 1
```

## 生成调度示例

```bash
python scripts/generate_scheduler_assets.py --hour 9 --minute 0
```

## 当前输出

- 每个来源的原始结果：`data/raw/<source>/<YYYY-MM-DD>/`
- 每个来源的处理结果：`data/processed/<source>/<YYYY-MM-DD>/`
- 合并结果：`data/processed/merged/<YYYY-MM-DD>/`
- 去重结果与重复报告：`data/processed/deduped/<YYYY-MM-DD>/`
- 排序结果：`data/processed/scored/<YYYY-MM-DD>/`
- Obsidian 条目笔记：`outputs/obsidian/papers/`、`projects/`、`inbox/`
- Obsidian 日报：`outputs/obsidian/dashboards/daily/<YYYY-MM-DD>/`
- Obsidian 周报：`outputs/obsidian/dashboards/weekly/<YYYY-Www>/`
- 失败条目：`outputs/debug/failed_items/<YYYY-MM-DD>/`
- 运行日志：`logs/runs/<YYYY-MM-DD>/`
- 已归档旧脚本和旧平铺数据：`archive/`
- 调度示例：`outputs/exports/markdown/scheduling/`

## 当前说明

- 默认模型当前为 `mistral:7b`
- 如果切换到 `qwen3.5:9b`，等待时间通常会更长
- 模型处理较慢时，终端会持续输出心跳和阶段进度，避免看起来像卡住
- `scheduler` 模式会加运行锁；如果进程异常退出，陈旧锁会优先尝试自动回收
