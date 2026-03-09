# AI Radar

本项目用于构建一个本地运行的 AI Radar / AI Research Intelligence System。当前已经进入 V2：在 `arXiv + GitHub + Ollama 总结` 的基础上，增加结构化评分、标签、推荐级别、排序后的日报和更完整的运行记录。

## 当前能力

- `arXiv` 最新论文抓取
- `GitHub` 仓库搜索与抓取
- 基于 Ollama 的中文总结
- 结构化评分、标签和推荐级别
- 结构化 `processed JSON` 输出
- `scored JSON` 输出
- Obsidian 条目笔记输出
- 每次运行生成日报与运行状态
- 日报按分数排序，并显示优先级
- 终端阶段日志和进度提示

## 目录说明

- `config/`：来源、模型、提示词、Obsidian 输出配置
- `data/`：原始数据、处理后数据、缓存和状态
- `outputs/`：Obsidian 输出、日报和调试信息
- `docs/`：工程文档
- `obsidian/`：项目知识库笔记
- `src/`：核心代码
- `scripts/`：辅助脚本

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

### 3. 运行一次

```bash
python run_once.py --max-items 2
```

### 4. 手动调试

```bash
python run_manual.py --sources arxiv github --max-items 3
```

## 说明

- 当前优先支持本地 `Ollama`
- 自动化调度仍处于预留阶段，细节会写入 `obsidian/` 与 `docs/`
- 重要过程记录见 Obsidian 笔记：`obsidian/00_Project/`

## V2 输出重点

- `data/processed/scored/`：按总分排序的结构化结果
- `outputs/obsidian/dashboards/`：带优先级排序的日报
- 条目笔记会展示：
  - 推荐级别
  - 总分
  - 分数拆解
  - 标签
  - 关注建议
