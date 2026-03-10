"""主题看板导出器。"""

from __future__ import annotations

import logging
from pathlib import Path

from src.models import SourceRunRecord, TopicCluster
from src.utils.file_ops import write_text
from src.utils.markdown_utils import bullet_items
from src.utils.obsidian_utils import build_wikilink
from src.utils.time_utils import date_slug


class DashboardExporter:
    """把主题聚合结果导出成 Obsidian 看板。"""

    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root
        self.dashboard_root = output_root / "dashboards"
        self.logger = logging.getLogger("exporter")

    def export_topic_dashboard(
        self,
        *,
        clusters: list[TopicCluster],
        records: list[SourceRunRecord],
        note_name: str,
        run_id: str,
        filtered_count: int,
        quality_report_path: str | None,
        daily_brief_note_name: str,
        archive_date: str | None = None,
    ) -> Path:
        """导出基于主题聚合的每日看板。"""

        day = archive_date or date_slug()
        sections: list[str] = [
            f"# {note_name}",
            "",
            f"关联：[[{daily_brief_note_name}]] | [[结果索引]] | [[版本迭代记录]] | [[会话日志]] | [[任务笔记 - AI Radar 搭建]]",
            "",
            "## 看板概览",
            f"- 运行 ID：`{run_id}`",
            f"- 主题数：{len(clusters)}",
            f"- 质量过滤移除条目：{filtered_count}",
            f"- 质量报告：`{quality_report_path or '无'}`",
            "",
            "## 来源质量快照",
            bullet_items(
                [
                    (
                        f"{record.source}：原始 {record.raw_count} 条，处理 {record.processed_count} 条，"
                        f"保留 {record.stage_stats.get('quality_kept', record.processed_count)} 条，"
                        f"过滤 {record.stage_stats.get('quality_filtered', 0)} 条"
                    )
                    for record in records
                ]
            )
            or "- 无",
            "",
            "## 主题聚合",
        ]

        if not clusters:
            sections.extend(["", "- 本轮没有形成可读的主题聚合结果。"])
        else:
            for cluster in clusters:
                sections.extend(
                    [
                        "",
                        f"### {cluster.topic_name}",
                        f"- 条目数：{cluster.item_count}",
                        f"- 平均分：{cluster.avg_score:.1f}",
                        f"- 最高分：{cluster.max_score:.1f}",
                        f"- 来源分布：{self._source_counts_text(cluster.source_counts)}",
                        f"- 主题摘要：{cluster.summary_cn}",
                        f"- 关键词：{', '.join(cluster.top_keywords) or '无'}",
                        "- 代表条目：",
                    ]
                )
                for item in cluster.items:
                    alias = item.get("title", "未知标题")
                    note_path = item.get("note_path")
                    link_text = (
                        build_wikilink(Path(note_path).stem, alias=alias) if note_path else alias
                    )
                    sections.append(
                        f"  - {link_text} | 来源 {item.get('source', '未知')} | 总分 {item.get('total_score', 0):.1f} | {item.get('priority_level', '未评级')}"
                    )

        path = write_text(self.dashboard_root / "daily" / day / f"{note_name}.md", "\n".join(sections))
        self.logger.info("导出主题看板 | path=%s", path)
        return path

    def _source_counts_text(self, source_counts: dict[str, int]) -> str:
        """把来源分布转换成可读文本。"""

        if not source_counts:
            return "无"
        return "、".join(f"{source} {count} 条" for source, count in sorted(source_counts.items()))
