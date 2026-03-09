"""JSON 导出器。"""

from __future__ import annotations

import logging
from pathlib import Path

from src.models import ProcessedItem, RawItem
from src.utils.file_ops import write_json


class JsonExporter:
    """负责把原始数据和处理结果写入 JSON。"""

    def __init__(self, raw_root: Path, processed_root: Path) -> None:
        self.raw_root = raw_root
        self.processed_root = processed_root
        self.logger = logging.getLogger("exporter")

    def export_raw(self, source: str, items: list[RawItem], run_id: str) -> Path:
        """导出某个来源的原始数据。"""

        path = write_json(
            self.raw_root / source / f"{source}_{run_id}.json",
            [item.to_dict() for item in items],
        )
        self.logger.info("导出 raw JSON | source=%s | path=%s", source, path)
        return path

    def export_processed(self, source: str, items: list[ProcessedItem], run_id: str) -> Path:
        """导出某个来源的处理后数据。"""

        path = write_json(
            self.processed_root / source / f"{source}_{run_id}.json",
            [item.to_dict() for item in items],
        )
        self.logger.info("导出 processed JSON | source=%s | path=%s", source, path)
        return path

    def export_merged(self, items: list[ProcessedItem], run_id: str) -> Path:
        """导出本次运行的合并结果。"""

        path = write_json(
            self.processed_root / "merged" / f"merged_{run_id}.json",
            [item.to_dict() for item in items],
        )
        self.logger.info("导出 merged JSON | path=%s", path)
        return path

    def export_scored(self, items: list[ProcessedItem], run_id: str) -> Path:
        """导出按分数排序的结果。"""

        sorted_items = sorted(items, key=lambda item: item.total_score, reverse=True)
        path = write_json(
            self.processed_root / "scored" / f"scored_{run_id}.json",
            [item.to_dict() for item in sorted_items],
        )
        self.logger.info("导出 scored JSON | path=%s", path)
        return path
