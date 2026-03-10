"""失败条目回放与重试。"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console

from config.settings import AppSettings
from src.agents import (
    HeuristicDeduper,
    HeuristicScorer,
    KeywordTagger,
    LocalOllamaSummarizer,
    SourceQualityGate,
    TopicAggregator,
)
from src.exporters import DashboardExporter, DebugExporter, JsonExporter, ObsidianExporter
from src.models import FailedItemRecord, RawItem, SourceRunRecord
from src.utils.file_ops import read_json
from src.utils.time_utils import date_slug, now_local_iso, timestamp_slug


@dataclass(slots=True)
class ReplaySummary:
    """保存一次失败样本回放的摘要。"""

    run_id: str
    retried_count: int
    recovered_count: int
    failed_count: int
    skipped_count: int
    merged_path: str | None
    deduped_path: str | None
    scored_path: str | None
    dashboard_path: str | None
    topic_dashboard_path: str | None
    quality_report_path: str | None
    failed_items_path: str | None


class FailedItemReplayer:
    """把 failed_items 中可重试的总结失败条目重新跑一遍。"""

    def __init__(self, settings: AppSettings, console: Console) -> None:
        self.settings = settings
        self.console = console
        self.logger = logging.getLogger("app")
        self.run_id = timestamp_slug()
        self.archive_date = date_slug()
        self.json_exporter = JsonExporter(
            raw_root=settings.paths.raw_dir,
            processed_root=settings.paths.processed_dir,
        )
        self.debug_exporter = DebugExporter(settings.paths.debug_dir)
        self.obsidian_exporter = ObsidianExporter(settings.paths.obsidian_output_dir)
        self.dashboard_exporter = DashboardExporter(settings.paths.obsidian_output_dir)
        self.tagger = KeywordTagger(settings.scoring.get("tagging", {}))
        self.scorer = HeuristicScorer(settings.scoring.get("scoring", {}))
        self.quality_gate = SourceQualityGate(settings.scoring.get("quality_gate", {}))
        self.topic_aggregator = TopicAggregator(settings.scoring.get("dashboard", {}))
        self.deduper = HeuristicDeduper()
        self.summarizer = LocalOllamaSummarizer(
            host=self._ollama_host(),
            default_model=settings.models.get("default_model", "qwen3.5:9b"),
            fallback_models=settings.models.get("fallback_models", []),
            request_options=settings.models.get("request", {}),
            prompt_template=settings.prompts.get("summary_template", ""),
            system_prompt=settings.prompts.get("system_prompt", ""),
            debug_dir=settings.paths.debug_dir,
            console=console,
        )

    def replay_failed_file(self, failed_file: Path, max_items: int | None = None) -> ReplaySummary:
        """回放失败文件中的可重试条目。"""

        payloads = read_json(failed_file, [])
        raw_items, skipped_count = self._collect_retriable_raw_items(payloads=payloads, max_items=max_items)
        if not raw_items:
            return ReplaySummary(
                run_id=self.run_id,
                retried_count=0,
                recovered_count=0,
                failed_count=0,
                skipped_count=skipped_count,
                merged_path=None,
                deduped_path=None,
                scored_path=None,
                dashboard_path=None,
                topic_dashboard_path=None,
                quality_report_path=None,
                failed_items_path=None,
            )

        for source_name, source_items in self._group_raw_items_by_source(raw_items).items():
            self.json_exporter.export_raw(
                source=source_name,
                items=source_items,
                run_id=self.run_id,
                archive_date=self.archive_date,
            )

        summarization_result = self.summarizer.summarize_items(
            items=raw_items,
            run_id=self.run_id,
            archive_date=self.archive_date,
        )
        processed_items = self.scorer.score_items(
            self.tagger.tag_items(summarization_result.processed_items)
        )
        quality_result = self.quality_gate.filter_items(processed_items)
        processed_items = quality_result.kept_items
        source_records = self._build_source_records(
            raw_items=raw_items,
            processed_items=summarization_result.processed_items,
            failed_items=summarization_result.failed_items,
        )

        for record in source_records:
            source_items = [item for item in quality_result.kept_items + quality_result.filtered_items if item.source == record.source]
            record.processed_count = len(source_items)
            record.stage_stats["scored"] = len(source_items)
            record.stage_stats["quality_kept"] = len([item for item in source_items if item.quality_decision == "keep"])
            record.stage_stats["quality_filtered"] = len([item for item in source_items if item.quality_decision == "filter"])

        for source_name, source_items in self._group_processed_items_by_source(
            quality_result.kept_items + quality_result.filtered_items
        ).items():
            self.json_exporter.export_processed(
                source=source_name,
                items=source_items,
                run_id=self.run_id,
                archive_date=self.archive_date,
            )

        merged_path = str(
            self.json_exporter.export_merged(
                items=processed_items,
                run_id=self.run_id,
                archive_date=self.archive_date,
            )
        )
        dedupe_result = self.deduper.dedupe_items(processed_items)
        deduped_items = dedupe_result.unique_items
        topic_clusters = self.topic_aggregator.build_clusters(deduped_items)
        self.json_exporter.export_duplicate_report(
            duplicates=dedupe_result.duplicates,
            run_id=self.run_id,
            archive_date=self.archive_date,
        )
        export_result = self.obsidian_exporter.export_items(
            items=deduped_items,
            dashboard_note_name=f"失败重试 - {self.archive_date} - {self.run_id}",
            run_id=self.run_id,
        )
        deduped_path = str(
            self.json_exporter.export_deduped(
                items=deduped_items,
                run_id=self.run_id,
                archive_date=self.archive_date,
            )
        )
        scored_path = str(
            self.json_exporter.export_scored(
                items=deduped_items,
                run_id=self.run_id,
                archive_date=self.archive_date,
            )
        )
        self._update_source_records_after_export(
            source_records=source_records,
            deduped_items=deduped_items,
            failed_items=summarization_result.failed_items + export_result.failed_items,
        )
        quality_report_path = str(
            self.debug_exporter.export_quality_report(
                run_id=self.run_id,
                decisions=quality_result.decisions,
                archive_date=self.archive_date,
            )
        )
        topic_dashboard_path = str(
            self.dashboard_exporter.export_topic_dashboard(
                clusters=topic_clusters,
                records=source_records,
                note_name=f"失败重试主题看板 - {self.archive_date} - {self.run_id}",
                run_id=self.run_id,
                filtered_count=len(quality_result.filtered_items),
                quality_report_path=quality_report_path,
                daily_brief_note_name=f"失败重试 - {self.archive_date} - {self.run_id}",
                archive_date=self.archive_date,
            )
        )
        dashboard_path = str(
            self.obsidian_exporter.export_daily_brief(
                records=source_records,
                items=deduped_items,
                note_name=f"失败重试 - {self.archive_date} - {self.run_id}",
                run_id=self.run_id,
                total_processed=len(quality_result.kept_items + quality_result.filtered_items),
                duplicate_count=len(dedupe_result.duplicates),
                filtered_count=len(quality_result.filtered_items),
                topic_dashboard_note_name=f"失败重试主题看板 - {self.archive_date} - {self.run_id}",
                archive_date=self.archive_date,
            )
        )
        failed_items_path = str(
            self.debug_exporter.export_failed_items(
                run_id=self.run_id,
                failures=summarization_result.failed_items + export_result.failed_items,
                archive_date=self.archive_date,
            )
        )

        return ReplaySummary(
            run_id=self.run_id,
            retried_count=len(raw_items),
            recovered_count=len(deduped_items),
            failed_count=len(summarization_result.failed_items) + len(export_result.failed_items),
            skipped_count=skipped_count,
            merged_path=merged_path,
            deduped_path=deduped_path,
            scored_path=scored_path,
            dashboard_path=dashboard_path,
            topic_dashboard_path=topic_dashboard_path,
            quality_report_path=quality_report_path,
            failed_items_path=failed_items_path,
        )

    def _collect_retriable_raw_items(
        self,
        payloads: list[dict[str, Any]],
        max_items: int | None = None,
    ) -> tuple[list[RawItem], int]:
        """从失败记录中提取可重试的原始条目。"""

        raw_items: list[RawItem] = []
        skipped_count = 0
        for payload in payloads:
            if max_items is not None and len(raw_items) >= max_items:
                break

            if payload.get("stage") != "summarize":
                skipped_count += 1
                continue
            raw_item_payload = payload.get("extra", {}).get("raw_item")
            if not isinstance(raw_item_payload, dict):
                skipped_count += 1
                continue
            raw_items.append(
                RawItem(
                    source=raw_item_payload.get("source", "unknown"),
                    item_id=raw_item_payload.get("item_id", "unknown"),
                    title=raw_item_payload.get("title", "未知标题"),
                    url=raw_item_payload.get("url", ""),
                    published_at=raw_item_payload.get("published_at"),
                    authors=raw_item_payload.get("authors", []),
                    content=raw_item_payload.get("content", ""),
                    extra=raw_item_payload.get("extra", {}),
                )
            )
        return raw_items, skipped_count

    def _group_raw_items_by_source(self, items: list[RawItem]) -> dict[str, list[RawItem]]:
        """按来源分组原始条目。"""

        grouped: dict[str, list[RawItem]] = defaultdict(list)
        for item in items:
            grouped[item.source].append(item)
        return grouped

    def _group_processed_items_by_source(self, items: list) -> dict[str, list]:
        """按来源分组处理后条目。"""

        grouped: dict[str, list] = defaultdict(list)
        for item in items:
            grouped[item.source].append(item)
        return grouped

    def _build_source_records(
        self,
        raw_items: list[RawItem],
        processed_items: list,
        failed_items: list[FailedItemRecord],
    ) -> list[SourceRunRecord]:
        """为回放生成来源记录。"""

        raw_grouped = self._group_raw_items_by_source(raw_items)
        processed_grouped = self._group_processed_items_by_source(processed_items)
        failed_grouped: dict[str, list[FailedItemRecord]] = defaultdict(list)
        for item in failed_items:
            failed_grouped[item.source].append(item)

        source_records: list[SourceRunRecord] = []
        for source_name in sorted(raw_grouped):
            source_records.append(
                SourceRunRecord(
                    source=source_name,
                    raw_count=len(raw_grouped[source_name]),
                    processed_count=len(processed_grouped.get(source_name, [])),
                    started_at=now_local_iso(),
                    completed_at=now_local_iso(),
                    duration_seconds=0.0,
                    stage_stats={
                        "collected": len(raw_grouped[source_name]),
                        "summarized": len(processed_grouped.get(source_name, [])),
                        "tagged": len(processed_grouped.get(source_name, [])),
                        "scored": len(processed_grouped.get(source_name, [])),
                        "deduped": 0,
                        "exported": 0,
                        "failed": len(failed_grouped.get(source_name, [])),
                    },
                    errors=[failure.error for failure in failed_grouped.get(source_name, [])],
                )
            )
        return source_records

    def _update_source_records_after_export(
        self,
        source_records: list[SourceRunRecord],
        deduped_items: list,
        failed_items: list[FailedItemRecord],
    ) -> None:
        """把去重和导出结果回写到来源记录。"""

        deduped_grouped = self._group_processed_items_by_source(deduped_items)
        failed_grouped: dict[str, list[FailedItemRecord]] = defaultdict(list)
        for item in failed_items:
            failed_grouped[item.source].append(item)

        for record in source_records:
            source_items = deduped_grouped.get(record.source, [])
            record.stage_stats["deduped"] = len(source_items)
            record.note_paths = [item.note_path for item in source_items if item.note_path]
            record.stage_stats["exported"] = len(record.note_paths)
            record.stage_stats["failed"] = len(failed_grouped.get(record.source, []))
            record.errors = [failure.error for failure in failed_grouped.get(record.source, [])]

    def _ollama_host(self) -> str:
        """读取模型服务地址。"""

        import os

        return os.getenv("OLLAMA_HOST", "http://localhost:11434")
