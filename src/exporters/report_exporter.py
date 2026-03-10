"""通用 Markdown 报告导出器。"""

from __future__ import annotations

import logging
from pathlib import Path

from src.utils.file_ops import write_text
from src.utils.time_utils import week_slug


class ReportExporter:
    """负责把日报、周报等 Markdown 文本写入 reports 目录。"""

    def __init__(self, reports_root: Path) -> None:
        self.reports_root = reports_root
        self.logger = logging.getLogger("exporter")

    def export_weekly_report(
        self,
        note_name: str,
        content: str,
        archive_week: str | None = None,
    ) -> Path:
        """导出周报 Markdown 文件。"""

        week = archive_week or week_slug()
        path = write_text(self.reports_root / "weekly" / week / f"{note_name}.md", content)
        self.logger.info("导出 weekly report | path=%s", path)
        return path
