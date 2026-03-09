"""Obsidian Markdown 导出器。"""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from src.models import ProcessedItem, SourceRunRecord
from src.utils.file_ops import write_text
from src.utils.markdown_utils import bullet_items, quote_block
from src.utils.obsidian_utils import build_note_name, build_wikilink
from src.utils.time_utils import date_slug


class ObsidianExporter:
    """把处理结果导出成 Obsidian 可读笔记。"""

    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root
        self.papers_dir = output_root / "papers"
        self.projects_dir = output_root / "projects"
        self.dashboard_dir = output_root / "dashboards"
        self.logger = logging.getLogger("exporter")

    def export_items(self, items: list[ProcessedItem], dashboard_note_name: str) -> list[str]:
        """导出单条内容笔记。"""

        note_paths: list[str] = []
        for item in self._sorted_items(items):
            note_name = build_note_name(self._note_prefix(item.source), item.title)
            note_path = self._target_dir(item.source) / f"{note_name}.md"
            content = self._render_item_note(item=item, note_name=note_name, dashboard_note_name=dashboard_note_name)
            write_text(note_path, content)
            item.note_path = str(note_path)
            note_paths.append(str(note_path))
            self.logger.info("导出 Obsidian 条目笔记 | source=%s | path=%s", item.source, note_path)
        return note_paths

    def export_daily_brief(
        self,
        records: list[SourceRunRecord],
        items: list[ProcessedItem],
        note_name: str,
        run_id: str,
    ) -> Path:
        """导出日报总览笔记。"""

        grouped_items: dict[str, list[ProcessedItem]] = defaultdict(list)
        for item in items:
            grouped_items[item.source].append(item)

        sorted_all_items = self._sorted_items(items)

        sections: list[str] = [
            f"# {note_name}",
            "",
            "关联：[[结果索引]] | [[版本迭代记录]] | [[会话日志]] | [[任务笔记 - AI Radar 搭建]]",
            "",
            "## 本次运行概览",
            f"- 运行 ID：`{run_id}`",
            f"- 来源：{', '.join(record.source for record in records)}",
            f"- 总条目数：{len(items)}",
            "",
            "## 来源统计",
            bullet_items(
                [
                    f"{record.source}：原始 {record.raw_count} 条，处理 {record.processed_count} 条，耗时 {record.duration_seconds or 0:.1f} 秒"
                    for record in records
                ]
            ),
            "",
            "## 本次优先级最高的内容",
            bullet_items(
                [
                    f"{build_wikilink(Path(item.note_path).stem, alias=item.title)} | 总分 {item.total_score:.1f} | {item.priority_level}"
                    for item in sorted_all_items[:5]
                    if item.note_path
                ]
            ),
            "",
            "## 值得关注的内容",
        ]

        for source_name in sorted(grouped_items):
            sections.append("")
            sections.append(f"### {source_name}")
            for item in self._sorted_items(grouped_items[source_name]):
                note_name_for_link = Path(item.note_path).stem if item.note_path else item.title
                sections.append(
                    f"- {build_wikilink(note_name_for_link, alias=item.title)} | 总分 {item.total_score:.1f} | {item.priority_level} | 标签：{', '.join(item.tags[:4]) or '无'}：{item.why_it_matters_cn or item.content_overview_cn}"
                )

        path = write_text(self.dashboard_dir / f"{note_name}.md", "\n".join(sections))
        self.logger.info("导出 Obsidian 日报 | path=%s", path)
        return path

    def _render_item_note(self, item: ProcessedItem, note_name: str, dashboard_note_name: str) -> str:
        """渲染单条内容笔记。"""

        metadata_lines = [
            f"来源：{item.source}",
            f"标题：{item.title}",
            f"链接：{item.url}",
            f"时间：{item.published_at or '未知'}",
            f"作者 / 维护者：{', '.join(author for author in item.authors if author) or '未知'}",
            f"使用模型：{item.model_name}",
        ]

        if item.source == "arxiv" and item.extra.get("pdf_url"):
            metadata_lines.append(f"PDF：{item.extra['pdf_url']}")
        if item.source == "github":
            metadata_lines.append(f"Stars：{item.extra.get('stars', '未知')}")
            metadata_lines.append(f"语言：{item.extra.get('language', '未知')}")

        sections = [
            f"# {note_name}",
            "",
            f"关联：[[{dashboard_note_name}]] | [[结果索引]] | [[任务笔记 - AI Radar 搭建]]",
            "",
            "## V2 结论",
            bullet_items(
                [
                    f"推荐级别：{item.priority_level}",
                    f"总分：{item.total_score:.1f}",
                    f"关注建议：{item.recommendation_cn or '无'}",
                    f"评分理由：{item.score_reason_cn or '无'}",
                ]
            ),
            "",
            "## 基本信息",
            bullet_items(metadata_lines),
            "",
            "## 标签",
            bullet_items(item.tags),
            "",
            "## 分数拆解",
            bullet_items(
                [
                    f"新颖性：{item.score_breakdown.get('novelty', 0):.1f}",
                    f"落地信号：{item.score_breakdown.get('execution_signal', 0):.1f}",
                    f"个人相关性：{item.score_breakdown.get('personal_relevance', 0):.1f}",
                ]
            ),
            "",
            "## 中文总结",
            "### 内容概述",
            item.content_overview_cn or "无",
            "",
            "### 解决的问题",
            item.problem_cn or "无",
            "",
            "### 为什么值得关注",
            item.why_it_matters_cn or "无",
            "",
            "### 适合我关注的原因",
            item.why_follow_cn or "无",
            "",
            "### 关键词",
            bullet_items(item.keywords),
            "",
            "### 简洁引用",
            quote_block(item.quote_cn or "无"),
            "",
            "## 原始内容",
            item.raw_content or "无",
            "",
            "## 调试信息",
            bullet_items(
                [
                    f"Prompt：`{item.prompt_path or '无'}`",
                    f"Response：`{item.response_path or '无'}`",
                ]
            ),
        ]

        return "\n".join(sections)

    def _note_prefix(self, source: str) -> str:
        """根据来源选择笔记前缀。"""

        return "论文" if source == "arxiv" else "项目"

    def _target_dir(self, source: str) -> Path:
        """根据来源选择导出目录。"""

        return self.papers_dir if source == "arxiv" else self.projects_dir

    def _sorted_items(self, items: list[ProcessedItem]) -> list[ProcessedItem]:
        """按分数和时间对条目排序。"""

        return sorted(
            items,
            key=lambda item: (item.total_score, item.published_at or ""),
            reverse=True,
        )
