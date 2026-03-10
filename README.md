# AI Radar

本项目用于构建一个本地运行的 AI Radar / AI Research Intelligence System。当前已经完成 V4 稳定版，并补做了一轮仓库整理：`arXiv + GitHub + RSS + Hacker News + News + Ollama 总结 + scoring/tags + merge/dedupe + failed_items + 日报/周报 + scheduler 预留` 都已跑通，历史结果也已经按日/按周重新归档。

## 当前能力

- `arXiv` 最新论文抓取
- `GitHub` 仓库搜索与抓取
- `RSS` 订阅抓取
- `Hacker News` 热门内容筛选
- `News` 新闻源抓取
- 基于 Ollama 的中文总结
- 结构化评分、标签和推荐级别
- 结构化 `processed JSON` 输出
- `deduped JSON`、`duplicate report`、`scored JSON`
- `failed_items JSON` 输出
- Obsidian 条目笔记输出
- 每次运行生成日报与运行状态
- 自动聚合最近 7 天运行日志生成周报
- scheduler 模式运行锁和 PID 元信息
- `cron / launchd` 示例配置生成
- `failed_items` 真实回放脚本
- 终端阶段日志、进度提示和模型等待心跳

## 目录说明

- `config/`：来源、模型、提示词、Obsidian 输出配置
- `data/`：原始数据、处理后数据、缓存和状态
- `outputs/`：Obsidian 输出、日报、周报和调试信息
- `docs/`：工程文档
- `obsidian/`：项目知识库笔记
- `src/`：核心代码
- `scripts/`：当前在用的辅助脚本
- `archive/`：已归档的旧验证脚本和早期平铺产物

## 运行方式

### 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 2. 可选：准备 `.env`

可参考 `.env.example`，目前支持：

- `OLLAMA_HOST`
- `OLLAMA_MODEL`
- `GITHUB_TOKEN`

默认模型当前设置为 `mistral:7b`。原因不是偏好，而是这台机器上的实测首轮响应明显比 `qwen3.5:9b` 更稳。如果你愿意接受更长等待，可以把 `OLLAMA_MODEL` 改成 `qwen3.5:9b`。

### 3. 检查 Ollama

```bash
python scripts/healthcheck_ollama.py
```

### 4. 运行一次

```bash
python run_once.py --max-items 2
```

### 5. 手动调试

```bash
python run_manual.py --sources arxiv github rss hackernews news --max-items 1
```

### 6. scheduler 模式预演

```bash
python run_ai_radar.py --max-items 1
```

### 7. 生成调度示例配置

```bash
python scripts/generate_scheduler_assets.py --hour 9 --minute 0
```

### 8. 回放失败条目

```bash
python scripts/retry_failed_items.py --failed-file outputs/debug/failed_items/<YYYY-MM-DD>/<failed_file>.json --max-items 1
```

## 说明

- 当前优先支持本地 `Ollama`
- 自动化调度仍处于预留阶段，细节会写入 `obsidian/` 与 `docs/`
- 重要过程记录见 Obsidian 笔记：`obsidian/00_Project/`
- `tests/` 里的正式自动化测试仍然保留，未做归档

## 当前归档结构

- `data/raw/<source>/<YYYY-MM-DD>/`：每天每个来源的原始抓取结果
- `data/processed/<source>/<YYYY-MM-DD>/`：每天每个来源的处理结果
- `data/processed/merged/<YYYY-MM-DD>/`：每日合并结果
- `data/processed/deduped/<YYYY-MM-DD>/`：每日去重结果和重复报告
- `data/processed/scored/<YYYY-MM-DD>/`：每日排序结果
- `outputs/obsidian/dashboards/daily/<YYYY-MM-DD>/`：Obsidian 日报
- `outputs/obsidian/dashboards/weekly/<YYYY-Www>/`：Obsidian 周报
- `outputs/reports/weekly/<YYYY-Www>/`：周报 Markdown 副本
- `outputs/debug/prompts/<YYYY-MM-DD>/`：每日 prompt 调试输出
- `outputs/debug/responses/<YYYY-MM-DD>/`：每日 response 调试输出
- `outputs/debug/failed_items/<YYYY-MM-DD>/`：每日失败条目索引
- `logs/runs/<YYYY-MM-DD>/`：每日运行日志
- `scripts/healthcheck_ollama.py`：当前可用的 Ollama 健康检查脚本
- `archive/scripts/test_ollama.py`：已归档的旧版测试命名脚本
- `archive/legacy/raw_flat/`：早期未按来源/日期分层的 raw JSON

## 当前输出重点

- `outputs/obsidian/inbox/`：资讯类条目笔记
- `outputs/exports/markdown/scheduling/`：cron / launchd 示例配置
- `scripts/retry_failed_items.py`：对真实失败样本做回放恢复
- 条目笔记会展示推荐级别、总分、分数拆解、标签和关注建议
