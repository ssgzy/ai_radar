"""调试输出导出器。"""

from __future__ import annotations

import logging
from pathlib import Path

from src.agents.quality_gate import QualityDecision
from src.models import FailedItemRecord
from src.utils.file_ops import write_json
from src.utils.time_utils import date_slug


class DebugExporter:
    """负责把失败条目等调试信息写入磁盘。"""

    def __init__(self, debug_root: Path) -> None:
        self.failed_items_dir = debug_root / "failed_items"
        self.quality_gate_dir = debug_root / "quality_gate"
        self.logger = logging.getLogger("errors")

    def export_failed_items(
        self,
        run_id: str,
        failures: list[FailedItemRecord],
        archive_date: str | None = None,
    ) -> Path:
        """导出本次运行的失败条目记录。"""

        day = archive_date or date_slug()
        path = write_json(
            self.failed_items_dir / day / f"failed_items_{run_id}.json",
            [failure.to_dict() for failure in failures],
        )
        self.logger.info("导出 failed items | run_id=%s | count=%s | path=%s", run_id, len(failures), path)
        return path

    def export_quality_report(
        self,
        run_id: str,
        decisions: list[QualityDecision],
        archive_date: str | None = None,
    ) -> Path:
        """导出本次运行的质量过滤报告。"""

        day = archive_date or date_slug()
        path = write_json(
            self.quality_gate_dir / day / f"quality_report_{run_id}.json",
            [decision.to_dict() for decision in decisions],
        )
        self.logger.info("导出 quality report | run_id=%s | count=%s | path=%s", run_id, len(decisions), path)
        return path
