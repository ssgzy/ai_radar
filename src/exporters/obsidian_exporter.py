"""Obsidian Markdown 导出器。"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.models import FailedItemRecord, ProcessedItem, SourceRunRecord
from src.utils.file_ops import write_text
from src.utils.markdown_utils import bullet_items, quote_block
from src.utils.obsidian_utils import build_note_name, build_wikilink
from src.utils.time_utils import date_slug, week_slug


@dataclass(slots=True)
class ExportResult:
    """保存条目导出的成功与失败结果。"""

    exported_items: list[ProcessedItem]
    note_paths: list[str]
    failed_items: list[FailedItemRecord]


class ObsidianExporter:
    """把处理结果导出成 Obsidian 可读笔记。"""

    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root
        self.inbox_dir = output_root / "inbox"
        self.papers_dir = output_root / "papers"
        self.projects_dir = output_root / "projects"
        self.dashboard_root = output_root / "dashboards"
        self.logger = logging.getLogger("exporter")

    def export_items(self, items: list[ProcessedItem], dashboard_note_name: str, run_id: str) -> ExportResult:
        """导出单条内容笔记。"""

        note_paths: list[str] = []
        exported_items: list[ProcessedItem] = []
        failed_items: list[FailedItemRecord] = []
        for item in self._sorted_items(items):
            note_name = build_note_name(self._note_prefix(item.source), item.title)
            note_path = self._target_dir(item.source) / f"{note_name}.md"
            try:
                content = self._render_item_note(
                    item=item,
                    note_name=note_name,
                    dashboard_note_name=dashboard_note_name,
                )
                write_text(note_path, content)
                item.note_path = str(note_path)
                note_paths.append(str(note_path))
                exported_items.append(item)
                self.logger.info("导出 Obsidian 条目笔记 | source=%s | path=%s", item.source, note_path)
            except Exception as error:  # noqa: BLE001
                failed_items.append(
                    FailedItemRecord(
                        run_id=run_id,
                        stage="export_item_note",
                        source=item.source,
                        title=item.title,
                        item_id=item.item_id,
                        url=item.url,
                        error=str(error),
                        created_at=datetime.now().astimezone().isoformat(timespec="seconds"),
                        prompt_path=item.prompt_path,
                        response_path=item.response_path,
                    )
                )
                logging.getLogger("errors").error(
                    "导出条目笔记失败 | source=%s | title=%s | error=%s",
                    item.source,
                    item.title,
                    error,
                )
        return ExportResult(exported_items=exported_items, note_paths=note_paths, failed_items=failed_items)

    def export_daily_brief(
        self,
        records: list[SourceRunRecord],
        items: list[ProcessedItem],
        note_name: str,
        run_id: str,
        total_processed: int,
        duplicate_count: int,
        filtered_count: int = 0,
        topic_dashboard_note_name: str | None = None,
        archive_date: str | None = None,
    ) -> Path:
        """导出日报总览笔记。"""

        day = archive_date or date_slug()
        grouped_items: dict[str, list[ProcessedItem]] = defaultdict(list)
        for item in items:
            grouped_items[item.source].append(item)

        sorted_all_items = self._sorted_items(items)

        sections: list[str] = [
            f"# {note_name}",
            "",
            "关联：[[结果索引]] | [[版本迭代记录]] | [[会话日志]] | [[任务笔记 - AI Radar 搭建]]"
            + (f" | [[{topic_dashboard_note_name}]]" if topic_dashboard_note_name else ""),
            "",
            "## 本次运行概览",
            f"- 运行 ID：`{run_id}`",
            f"- 来源：{', '.join(record.source for record in records)}",
            f"- 总条目数（去重后）：{len(items)}",
            f"- 去重前条目数：{total_processed}",
            f"- 质量过滤移除条目数：{filtered_count}",
            f"- 去重移除条目数：{duplicate_count}",
            "",
            "## 来源统计",
            bullet_items(
                [
                    f"{record.source}：原始 {record.raw_count} 条，处理 {record.processed_count} 条，保留 {record.stage_stats.get('quality_kept', record.processed_count)} 条，过滤 {record.stage_stats.get('quality_filtered', 0)} 条，去重后 {record.stage_stats.get('deduped', 0)} 条，耗时 {record.duration_seconds or 0:.1f} 秒"
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

        path = write_text(self.dashboard_root / "daily" / day / f"{note_name}.md", "\n".join(sections))
        self.logger.info("导出 Obsidian 日报 | path=%s", path)
        return path

    def build_weekly_brief_content(self, run_payloads: list[dict], note_name: str) -> str:
        """根据最近运行记录构建周报内容。"""

        ordered_payloads = sorted(
            run_payloads,
            key=lambda payload: payload.get("completed_at", ""),
            reverse=True,
        )
        source_totals: dict[str, dict[str, float]] = defaultdict(
            lambda: {"runs": 0, "processed": 0, "deduped": 0, "failed": 0}
        )
        top_items: dict[str, dict] = {}

        for payload in ordered_payloads:
            for record in payload.get("sources", []):
                bucket = source_totals[record.get("source", "unknown")]
                bucket["runs"] += 1
                bucket["processed"] += record.get("processed_count", 0)
                bucket["deduped"] += record.get("stage_stats", {}).get("deduped", 0)
                bucket["failed"] += record.get("stage_stats", {}).get("failed", 0)

            for item in payload.get("top_items", []):
                key = f"{item.get('source', 'unknown')}::{item.get('title', 'untitled')}"
                current = top_items.get(key)
                if current is None or item.get("total_score", 0) > current.get("total_score", 0):
                    top_items[key] = item

        start_at = ordered_payloads[-1].get("completed_at", "未知") if ordered_payloads else "未知"
        end_at = ordered_payloads[0].get("completed_at", "未知") if ordered_payloads else "未知"
        sorted_top_items = sorted(top_items.values(), key=lambda item: item.get("total_score", 0), reverse=True)

        sections = [
            f"# {note_name}",
            "",
            "关联：[[结果索引]] | [[版本迭代记录]] | [[会话日志]] | [[任务笔记 - AI Radar 搭建]]",
            "",
            "## 周报概览",
            f"- 纳入运行次数：{len(ordered_payloads)}",
            f"- 统计起点：`{start_at}`",
            f"- 统计终点：`{end_at}`",
            f"- 合计处理条目：{sum(payload.get('total_processed', 0) for payload in ordered_payloads)}",
            f"- 合计去重后条目：{sum(payload.get('total_deduped', 0) for payload in ordered_payloads)}",
            f"- 合计失败条目：{sum(payload.get('failed_items_count', 0) for payload in ordered_payloads)}",
            "",
            "## 来源汇总",
            bullet_items(
                [
                    f"{source}：运行 {int(values['runs'])} 次，处理 {int(values['processed'])} 条，去重后 {int(values['deduped'])} 条，失败 {int(values['failed'])} 条"
                    for source, values in sorted(source_totals.items())
                ]
            )
            or "- 无",
            "",
            "## 本周值得回看的内容",
            bullet_items(
                [
                    (
                        f"{build_wikilink(Path(item['note_path']).stem, alias=item['title'])}"
                        if item.get("note_path")
                        else f"{item.get('title', '未知标题')}"
                    )
                    + f" | 来源 {item.get('source', '未知')} | 总分 {item.get('total_score', 0):.1f} | {item.get('priority_level', '未评级')}"
                    for item in sorted_top_items[:10]
                ]
            )
            or "- 无",
            "",
            "## 运行记录",
            bullet_items(
                [
                    f"{payload.get('run_id', '未知')} | 模式 {payload.get('run_mode', '未知')} | 处理 {payload.get('total_processed', 0)} 条 | 去重后 {payload.get('total_deduped', 0)} 条 | 失败 {payload.get('failed_items_count', 0)} 条"
                    for payload in ordered_payloads
                ]
            )
            or "- 无",
        ]
        return "\n".join(sections)

    def export_weekly_brief(
        self,
        run_payloads: list[dict],
        note_name: str,
        archive_week: str | None = None,
    ) -> tuple[Path, str]:
        """导出 Obsidian 周报。"""

        week = archive_week or week_slug()
        content = self.build_weekly_brief_content(run_payloads=run_payloads, note_name=note_name)
        path = write_text(self.dashboard_root / "weekly" / week / f"{note_name}.md", content)
        self.logger.info("导出 Obsidian 周报 | path=%s", path)
        return path, content

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
        if item.topic_name:
            metadata_lines.append(f"主题：{item.topic_name}")
        metadata_lines.append(f"质量决策：{item.quality_decision}")
        if item.source == "github":
            metadata_lines.append(f"Stars：{item.extra.get('stars', '未知')}")
            metadata_lines.append(f"语言：{item.extra.get('language', '未知')}")
        if item.source in {"rss", "news"}:
            metadata_lines.append(f"Feed：{item.extra.get('feed_name', '未知')}")
        if item.source == "hackernews":
            metadata_lines.append(f"HN 分数：{item.extra.get('hn_score', 0)}")
            metadata_lines.append(f"HN 评论数：{item.extra.get('hn_comments', 0)}")
        if item.extra.get("duplicate_sources"):
            metadata_lines.append(f"合并来源数：{len(item.extra['duplicate_sources']) + 1}")

        sections = [
            f"# {note_name}",
            "",
            f"关联：[[{dashboard_note_name}]] | [[结果索引]] | [[任务笔记 - AI Radar 搭建]]",
            "",
            "## 结论与建议",
            bullet_items(
                [
                    f"推荐级别：{item.priority_level}",
                    f"总分：{item.total_score:.1f}",
                    f"关注建议：{item.recommendation_cn or '无'}",
                    f"评分理由：{item.score_reason_cn or '无'}",
                    f"质量说明：{item.quality_reason_cn or '无'}",
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

        if source == "arxiv":
            return "论文"
        if source == "github":
            return "项目"
        return "资讯"

    def _target_dir(self, source: str) -> Path:
        """根据来源选择导出目录。"""

        if source == "arxiv":
            return self.papers_dir
        if source == "github":
            return self.projects_dir
        return self.inbox_dir

    def _sorted_items(self, items: list[ProcessedItem]) -> list[ProcessedItem]:
        """按分数和时间对条目排序。"""

        return sorted(
            items,
            key=lambda item: (item.total_score, item.published_at or ""),
            reverse=True,
        )
