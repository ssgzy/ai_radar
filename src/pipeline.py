"""AI Radar 核心运行管线。"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

from config.settings import AppSettings
from src.agents import (
    HeuristicDeduper,
    HeuristicScorer,
    KeywordTagger,
    LocalOllamaSummarizer,
    SourceQualityGate,
    TopicAggregator,
)
from src.collectors import ArxivCollector, GitHubCollector, HackerNewsCollector, NewsCollector, RSSCollector
from src.exporters import DashboardExporter, DebugExporter, JsonExporter, ObsidianExporter, ReportExporter
from src.models import FailedItemRecord, ProcessedItem, SourceRunRecord, TopicCluster
from src.utils.file_ops import read_json, write_json
from src.utils.time_utils import date_slug, now_local_iso, timestamp_slug, week_slug


@dataclass(slots=True)
class RunSummary:
    """保存一次完整运行的摘要信息。"""

    run_id: str
    run_mode: str
    source_records: list[SourceRunRecord]
    total_processed: int
    total_kept: int
    total_deduped: int
    filtered_items_count: int
    failed_items_count: int
    merged_path: str | None
    deduped_path: str | None
    duplicate_report_path: str | None
    scored_path: str | None
    daily_brief_path: str | None
    topic_dashboard_path: str | None
    weekly_brief_path: str | None
    quality_report_path: str | None
    failed_items_path: str | None
    duration_seconds: float


class AIRadarPipeline:
    """串联采集、总结、导出和状态保存。"""

    def __init__(
        self,
        settings: AppSettings,
        console: Console,
        requested_sources: list[str] | None = None,
        max_items_override: int | None = None,
        run_mode: str = "scheduler",
    ) -> None:
        self.settings = settings
        self.console = console
        self.logger = logging.getLogger("app")
        self.requested_sources = requested_sources
        self.max_items_override = max_items_override
        self.run_mode = run_mode
        self.run_id = timestamp_slug()
        self.archive_date = date_slug()
        self.archive_week = week_slug()
        self.runtime_context: dict[str, Any] | None = None
        self.json_exporter = JsonExporter(
            raw_root=settings.paths.raw_dir,
            processed_root=settings.paths.processed_dir,
        )
        self.debug_exporter = DebugExporter(settings.paths.debug_dir)
        self.obsidian_exporter = ObsidianExporter(settings.paths.obsidian_output_dir)
        self.dashboard_exporter = DashboardExporter(settings.paths.obsidian_output_dir)
        self.report_exporter = ReportExporter(settings.paths.outputs_dir / "reports")
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
        self.collector_registry = {
            "arxiv": ArxivCollector,
            "github": GitHubCollector,
            "rss": RSSCollector,
            "hackernews": HackerNewsCollector,
            "news": NewsCollector,
        }

    def run(self) -> RunSummary:
        """执行完整 V4 流程。"""

        run_started_monotonic = time.monotonic()
        run_started_at = now_local_iso()
        dashboard_note_name = f"AI Radar 日报 - {self.archive_date} - {self.run_id}"
        topic_dashboard_note_name = f"AI Radar 主题看板 - {self.archive_date} - {self.run_id}"
        weekly_note_name = f"AI Radar 周报 - {self.archive_week}"
        all_processed_items: list[ProcessedItem] = []
        quality_kept_items: list[ProcessedItem] = []
        quality_decisions = []
        failed_items: list[FailedItemRecord] = []
        source_records: list[SourceRunRecord] = []
        self.logger.info("运行开始 | run_id=%s | mode=%s", self.run_id, self.run_mode)

        self.console.print(
            Panel.fit(
                f"运行模式：{self.run_mode}\n运行 ID：{self.run_id}",
                title="AI Radar V5",
            )
        )

        for source_name in self._enabled_sources():
            source_started_monotonic = time.monotonic()
            source_started_at = now_local_iso()
            stage_stats = {
                "collected": 0,
                "summarized": 0,
                "tagged": 0,
                "scored": 0,
                "quality_kept": 0,
                "quality_filtered": 0,
                "deduped": 0,
                "exported": 0,
                "failed": 0,
            }
            source_errors: list[str] = []
            source_all_items: list[ProcessedItem] = []
            raw_path: str | None = None
            processed_path: str | None = None
            self.logger.info("开始处理来源 | source=%s", source_name)

            try:
                collector = self.collector_registry[source_name](
                    source_config=self.settings.sources["sources"][source_name],
                    console=self.console,
                )
                raw_items = collector.collect(max_items=self.max_items_override)
                raw_path = str(
                    self.json_exporter.export_raw(
                        source=source_name,
                        items=raw_items,
                        run_id=self.run_id,
                        archive_date=self.archive_date,
                    )
                )
            except Exception as error:  # noqa: BLE001
                failed_items.append(
                    self._build_failure(
                        stage="collect",
                        source=source_name,
                        error=error,
                    )
                )
                source_errors.append(f"采集失败：{error}")
                source_records.append(
                    self._build_source_record(
                        source_name=source_name,
                        raw_count=0,
                        processed_count=0,
                        raw_path=raw_path,
                        processed_path=processed_path,
                        started_at=source_started_at,
                        source_started_monotonic=source_started_monotonic,
                        stage_stats=stage_stats,
                        errors=source_errors,
                    )
                )
                self.console.print(f"[red]来源失败[/red] {source_name} | {error}")
                logging.getLogger("errors").error("采集失败 | source=%s | error=%s", source_name, error)
                continue

            stage_stats["collected"] = len(raw_items)
            if not raw_items:
                source_errors.append("没有采集到条目")
                source_records.append(
                    self._build_source_record(
                        source_name=source_name,
                        raw_count=0,
                        processed_count=0,
                        raw_path=raw_path,
                        processed_path=processed_path,
                        started_at=source_started_at,
                        source_started_monotonic=source_started_monotonic,
                        stage_stats=stage_stats,
                        errors=source_errors,
                    )
                )
                continue

            summarization_result = self.summarizer.summarize_items(
                items=raw_items,
                run_id=self.run_id,
                archive_date=self.archive_date,
            )
            processed_items = summarization_result.processed_items
            failed_items.extend(summarization_result.failed_items)
            stage_stats["summarized"] = len(processed_items)
            stage_stats["failed"] += len(summarization_result.failed_items)

            try:
                processed_items = self.tagger.tag_items(processed_items)
                stage_stats["tagged"] = len(processed_items)
            except Exception as error:  # noqa: BLE001
                failed_items.append(
                    self._build_failure(
                        stage="tag",
                        source=source_name,
                        error=error,
                        extra={"raw_count": len(raw_items)},
                    )
                )
                source_errors.append(f"标签阶段失败：{error}")
                stage_stats["failed"] += 1
                logging.getLogger("errors").error("标签失败 | source=%s | error=%s", source_name, error)

            try:
                processed_items = self.scorer.score_items(processed_items)
                stage_stats["scored"] = len(processed_items)
                source_all_items = list(processed_items)
            except Exception as error:  # noqa: BLE001
                failed_items.append(
                    self._build_failure(
                        stage="score",
                        source=source_name,
                        error=error,
                        extra={"processed_count": len(processed_items)},
                    )
                )
                source_errors.append(f"评分阶段失败：{error}")
                stage_stats["failed"] += 1
                logging.getLogger("errors").error("评分失败 | source=%s | error=%s", source_name, error)

            if processed_items:
                quality_result = self.quality_gate.filter_items(processed_items)
                quality_decisions.extend(quality_result.decisions)
                stage_stats["quality_kept"] = len(quality_result.kept_items)
                stage_stats["quality_filtered"] = len(quality_result.filtered_items)
                if not quality_result.kept_items and quality_result.filtered_items:
                    source_errors.append("质量过滤后无保留条目")
                processed_items = quality_result.kept_items
                try:
                    processed_path = str(
                        self.json_exporter.export_processed(
                            source=source_name,
                            items=quality_result.kept_items + quality_result.filtered_items,
                            run_id=self.run_id,
                            archive_date=self.archive_date,
                        )
                    )
                except Exception as error:  # noqa: BLE001
                    failed_items.append(
                        self._build_failure(
                            stage="export_processed_json",
                            source=source_name,
                            error=error,
                        )
                    )
                    source_errors.append(f"处理结果导出失败：{error}")
                    stage_stats["failed"] += 1
                    logging.getLogger("errors").error(
                        "处理结果导出失败 | source=%s | error=%s", source_name, error
                    )

            all_processed_items.extend(source_all_items)
            quality_kept_items.extend(processed_items)
            source_records.append(
                self._build_source_record(
                    source_name=source_name,
                    raw_count=len(raw_items),
                    processed_count=stage_stats["scored"],
                    raw_path=raw_path,
                    processed_path=processed_path,
                    started_at=source_started_at,
                    source_started_monotonic=source_started_monotonic,
                    stage_stats=stage_stats,
                    errors=source_errors,
                )
            )

            self.console.print(
                f"[green]来源完成[/green] {source_name} | raw={len(raw_items)} | kept={stage_stats['quality_kept']} | filtered={stage_stats['quality_filtered']} | failed={stage_stats['failed']}"
            )
            self.logger.info(
                "来源完成 | source=%s | raw=%s | kept=%s | filtered=%s | failed=%s",
                source_name,
                len(raw_items),
                stage_stats["quality_kept"],
                stage_stats["quality_filtered"],
                stage_stats["failed"],
            )

        filtered_items_count = len(all_processed_items) - len(quality_kept_items)
        merged_path = None
        deduped_path = None
        duplicate_report_path = None
        scored_path = None
        daily_brief_path = None
        topic_dashboard_path = None
        weekly_brief_path = None
        weekly_report_path = None
        failed_items_path = None
        quality_report_path = None
        deduped_items: list[ProcessedItem] = []
        topic_clusters: list[TopicCluster] = []
        duplicate_count = 0

        if quality_kept_items:
            try:
                merged_path = str(
                    self.json_exporter.export_merged(
                        items=quality_kept_items,
                        run_id=self.run_id,
                        archive_date=self.archive_date,
                    )
                )
            except Exception as error:  # noqa: BLE001
                failed_items.append(self._build_failure(stage="export_merged_json", source="merged", error=error))
                logging.getLogger("errors").error("导出 merged JSON 失败 | error=%s", error)

            dedupe_result = self.deduper.dedupe_items(quality_kept_items)
            deduped_items = dedupe_result.unique_items
            duplicate_count = len(dedupe_result.duplicates)

            try:
                duplicate_report_path = str(
                    self.json_exporter.export_duplicate_report(
                        duplicates=dedupe_result.duplicates,
                        run_id=self.run_id,
                        archive_date=self.archive_date,
                    )
                )
            except Exception as error:  # noqa: BLE001
                failed_items.append(self._build_failure(stage="export_duplicate_report", source="deduped", error=error))
                logging.getLogger("errors").error("导出 duplicate report 失败 | error=%s", error)

            export_result = self.obsidian_exporter.export_items(
                items=deduped_items,
                dashboard_note_name=dashboard_note_name,
                run_id=self.run_id,
            )
            failed_items.extend(export_result.failed_items)
            self._update_source_records_after_dedupe(
                source_records=source_records,
                deduped_items=deduped_items,
                failed_items=export_result.failed_items,
            )
            topic_clusters = self.topic_aggregator.build_clusters(deduped_items)

            try:
                deduped_path = str(
                    self.json_exporter.export_deduped(
                        items=deduped_items,
                        run_id=self.run_id,
                        archive_date=self.archive_date,
                    )
                )
            except Exception as error:  # noqa: BLE001
                failed_items.append(self._build_failure(stage="export_deduped_json", source="deduped", error=error))
                logging.getLogger("errors").error("导出 deduped JSON 失败 | error=%s", error)

            try:
                scored_path = str(
                    self.json_exporter.export_scored(
                        items=deduped_items,
                        run_id=self.run_id,
                        archive_date=self.archive_date,
                    )
                )
            except Exception as error:  # noqa: BLE001
                failed_items.append(self._build_failure(stage="export_scored_json", source="scored", error=error))
                logging.getLogger("errors").error("导出 scored JSON 失败 | error=%s", error)

        try:
            quality_report_path = str(
                self.debug_exporter.export_quality_report(
                    run_id=self.run_id,
                    decisions=quality_decisions,
                    archive_date=self.archive_date,
                )
            )
        except Exception as error:  # noqa: BLE001
            failed_items.append(self._build_failure(stage="export_quality_report", source="quality_gate", error=error))
            logging.getLogger("errors").error("导出质量报告失败 | error=%s", error)

        try:
            topic_dashboard_path = str(
                self.dashboard_exporter.export_topic_dashboard(
                    clusters=topic_clusters,
                    records=source_records,
                    note_name=topic_dashboard_note_name,
                    run_id=self.run_id,
                    filtered_count=filtered_items_count,
                    quality_report_path=quality_report_path,
                    daily_brief_note_name=dashboard_note_name,
                    archive_date=self.archive_date,
                )
            )
        except Exception as error:  # noqa: BLE001
            failed_items.append(self._build_failure(stage="export_topic_dashboard", source="dashboard", error=error))
            logging.getLogger("errors").error("导出主题看板失败 | error=%s", error)

        try:
            daily_brief_path = str(
                self.obsidian_exporter.export_daily_brief(
                    records=source_records,
                    items=deduped_items,
                    note_name=dashboard_note_name,
                    run_id=self.run_id,
                    total_processed=len(all_processed_items),
                    duplicate_count=duplicate_count,
                    filtered_count=filtered_items_count,
                    topic_dashboard_note_name=topic_dashboard_note_name,
                    archive_date=self.archive_date,
                )
            )
        except Exception as error:  # noqa: BLE001
            failed_items.append(self._build_failure(stage="export_daily_brief", source="dashboard", error=error))
            logging.getLogger("errors").error("导出日报失败 | error=%s", error)

        interim_duration_seconds = round(time.monotonic() - run_started_monotonic, 2)
        interim_payload = self._build_run_payload(
            source_records=source_records,
            deduped_items=deduped_items,
            topic_clusters=topic_clusters,
            failed_items=failed_items,
            started_at=run_started_at,
            duration_seconds=interim_duration_seconds,
            duplicate_count=duplicate_count,
            merged_path=merged_path,
            deduped_path=deduped_path,
            duplicate_report_path=duplicate_report_path,
            scored_path=scored_path,
            daily_brief_path=daily_brief_path,
            topic_dashboard_path=topic_dashboard_path,
            weekly_brief_path=None,
            weekly_report_path=None,
            quality_report_path=quality_report_path,
            failed_items_path=None,
            total_processed=len(all_processed_items),
            total_kept=len(quality_kept_items),
            filtered_items_count=filtered_items_count,
        )

        try:
            recent_payloads = self._load_recent_run_payloads(days=7)
            weekly_brief_path_obj, weekly_content = self.obsidian_exporter.export_weekly_brief(
                run_payloads=recent_payloads + [interim_payload],
                note_name=weekly_note_name,
                archive_week=self.archive_week,
            )
            weekly_brief_path = str(weekly_brief_path_obj)
            weekly_report_path = str(
                self.report_exporter.export_weekly_report(
                    note_name=weekly_note_name,
                    content=weekly_content,
                    archive_week=self.archive_week,
                )
            )
        except Exception as error:  # noqa: BLE001
            failed_items.append(self._build_failure(stage="export_weekly_brief", source="dashboard", error=error))
            logging.getLogger("errors").error("导出周报失败 | error=%s", error)

        try:
            failed_items_path = str(
                self.debug_exporter.export_failed_items(
                    run_id=self.run_id,
                    failures=failed_items,
                    archive_date=self.archive_date,
                )
            )
        except Exception as error:  # noqa: BLE001
            logging.getLogger("errors").error("导出 failed_items 失败 | error=%s", error)

        total_duration_seconds = round(time.monotonic() - run_started_monotonic, 2)
        final_payload = self._build_run_payload(
            source_records=source_records,
            deduped_items=deduped_items,
            topic_clusters=topic_clusters,
            failed_items=failed_items,
            started_at=run_started_at,
            duration_seconds=total_duration_seconds,
            duplicate_count=duplicate_count,
            merged_path=merged_path,
            deduped_path=deduped_path,
            duplicate_report_path=duplicate_report_path,
            scored_path=scored_path,
            daily_brief_path=daily_brief_path,
            topic_dashboard_path=topic_dashboard_path,
            weekly_brief_path=weekly_brief_path,
            weekly_report_path=weekly_report_path,
            quality_report_path=quality_report_path,
            failed_items_path=failed_items_path,
            total_processed=len(all_processed_items),
            total_kept=len(quality_kept_items),
            filtered_items_count=filtered_items_count,
        )
        self._write_state(run_payload=final_payload, all_processed_items=all_processed_items)

        self.console.print(
            Panel.fit(
                f"处理条目：{len(all_processed_items)}\n质量保留：{len(quality_kept_items)}\n质量过滤：{filtered_items_count}\n去重后条目：{len(deduped_items)}\n失败条目：{len(failed_items)}\n运行耗时：{total_duration_seconds:.1f} 秒\nMerged JSON：{merged_path or '无'}\nDeduped JSON：{deduped_path or '无'}\nScored JSON：{scored_path or '无'}\n日报：{daily_brief_path or '无'}\n主题看板：{topic_dashboard_path or '无'}\n周报：{weekly_brief_path or '无'}",
                title="运行完成",
            )
        )
        self.logger.info(
            "运行完成 | run_id=%s | total_processed=%s | total_kept=%s | filtered=%s | total_deduped=%s | failed=%s | duration=%.2f | merged=%s | deduped=%s | scored=%s | daily=%s | topic_dashboard=%s | weekly=%s",
            self.run_id,
            len(all_processed_items),
            len(quality_kept_items),
            filtered_items_count,
            len(deduped_items),
            len(failed_items),
            total_duration_seconds,
            merged_path,
            deduped_path,
            scored_path,
            daily_brief_path,
            topic_dashboard_path,
            weekly_brief_path,
        )

        return RunSummary(
            run_id=self.run_id,
            run_mode=self.run_mode,
            source_records=source_records,
            total_processed=len(all_processed_items),
            total_kept=len(quality_kept_items),
            total_deduped=len(deduped_items),
            filtered_items_count=filtered_items_count,
            failed_items_count=len(failed_items),
            merged_path=merged_path,
            deduped_path=deduped_path,
            duplicate_report_path=duplicate_report_path,
            scored_path=scored_path,
            daily_brief_path=daily_brief_path,
            topic_dashboard_path=topic_dashboard_path,
            weekly_brief_path=weekly_brief_path,
            quality_report_path=quality_report_path,
            failed_items_path=failed_items_path,
            duration_seconds=total_duration_seconds,
        )

    def _enabled_sources(self) -> list[str]:
        """返回本次运行应该启用的来源列表。"""

        configured_sources = self.settings.sources.get("sources", {})
        names = [
            source_name
            for source_name, source_config in configured_sources.items()
            if source_config.get("enabled", False)
        ]
        if self.requested_sources:
            requested_set = set(self.requested_sources)
            names = [source_name for source_name in names if source_name in requested_set]
        return names

    def _build_failure(
        self,
        stage: str,
        source: str,
        error: Exception,
        *,
        title: str | None = None,
        item_id: str | None = None,
        url: str | None = None,
        prompt_path: str | None = None,
        response_path: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> FailedItemRecord:
        """构造统一的失败记录。"""

        return FailedItemRecord(
            run_id=self.run_id,
            stage=stage,
            source=source,
            title=title,
            item_id=item_id,
            url=url,
            error=str(error),
            created_at=now_local_iso(),
            prompt_path=prompt_path,
            response_path=response_path,
            extra=extra or {},
        )

    def _build_source_record(
        self,
        source_name: str,
        raw_count: int,
        processed_count: int,
        raw_path: str | None,
        processed_path: str | None,
        started_at: str,
        source_started_monotonic: float,
        stage_stats: dict[str, Any],
        errors: list[str],
    ) -> SourceRunRecord:
        """构造来源级运行记录。"""

        return SourceRunRecord(
            source=source_name,
            raw_count=raw_count,
            processed_count=processed_count,
            raw_path=raw_path,
            processed_path=processed_path,
            started_at=started_at,
            completed_at=now_local_iso(),
            duration_seconds=round(time.monotonic() - source_started_monotonic, 2),
            stage_stats=stage_stats,
            note_paths=[],
            errors=errors,
        )

    def _build_run_payload(
        self,
        *,
        source_records: list[SourceRunRecord],
        deduped_items: list[ProcessedItem],
        topic_clusters: list[TopicCluster],
        failed_items: list[FailedItemRecord],
        started_at: str,
        duration_seconds: float,
        duplicate_count: int,
        merged_path: str | None,
        deduped_path: str | None,
        duplicate_report_path: str | None,
        scored_path: str | None,
        daily_brief_path: str | None,
        topic_dashboard_path: str | None,
        weekly_brief_path: str | None,
        weekly_report_path: str | None,
        quality_report_path: str | None,
        failed_items_path: str | None,
        total_processed: int,
        total_kept: int,
        filtered_items_count: int,
    ) -> dict[str, Any]:
        """构造状态和运行日志共用的 payload。"""

        return {
            "run_id": self.run_id,
            "run_mode": self.run_mode,
            "started_at": started_at,
            "completed_at": now_local_iso(),
            "duration_seconds": duration_seconds,
            "sources": [record.to_dict() for record in source_records],
            "total_processed": total_processed,
            "total_kept": total_kept,
            "total_deduped": len(deduped_items),
            "filtered_items_count": filtered_items_count,
            "failed_items_count": len(failed_items),
            "duplicate_count": duplicate_count,
            "merged_path": merged_path,
            "deduped_path": deduped_path,
            "duplicate_report_path": duplicate_report_path,
            "scored_path": scored_path,
            "daily_brief_path": daily_brief_path,
            "brief_path": daily_brief_path,
            "topic_dashboard_path": topic_dashboard_path,
            "weekly_brief_path": weekly_brief_path,
            "weekly_report_path": weekly_report_path,
            "quality_report_path": quality_report_path,
            "failed_items_path": failed_items_path,
            "runtime_context": self.runtime_context or {},
            "top_items": [
                {
                    "title": item.title,
                    "source": item.source,
                    "total_score": item.total_score,
                    "priority_level": item.priority_level,
                    "topic_name": item.topic_name,
                    "note_path": item.note_path,
                }
                for item in sorted(deduped_items, key=lambda item: item.total_score, reverse=True)[:10]
            ],
            "top_topics": [cluster.to_dict() for cluster in topic_clusters],
        }

    def _write_state(self, run_payload: dict[str, Any], all_processed_items: list[ProcessedItem]) -> None:
        """写入运行状态和已见集合。"""

        state_dir = self.settings.paths.state_dir
        run_log_dir = self.settings.paths.logs_dir / "runs" / self.archive_date
        write_json(state_dir / "last_run.json", run_payload)
        write_json(run_log_dir / f"{self.run_id}.json", run_payload)

        seen_ids = read_json(state_dir / "seen_ids.json", {})
        seen_urls = read_json(state_dir / "seen_urls.json", {})
        seen_titles = read_json(state_dir / "seen_titles.json", {})
        source_checkpoints = read_json(state_dir / "source_checkpoints.json", {})

        for item in all_processed_items:
            seen_ids[item.item_id] = item.source
            seen_urls[item.url] = item.source
            seen_titles[item.title] = item.source
            source_checkpoints[item.source] = {
                "last_item_id": item.item_id,
                "last_title": item.title,
                "updated_at": now_local_iso(),
            }

        write_json(state_dir / "seen_ids.json", seen_ids)
        write_json(state_dir / "seen_urls.json", seen_urls)
        write_json(state_dir / "seen_titles.json", seen_titles)
        write_json(state_dir / "source_checkpoints.json", source_checkpoints)

    def _load_recent_run_payloads(self, days: int) -> list[dict[str, Any]]:
        """读取最近若干天的运行日志，用于生成周报。"""

        run_log_dir = self.settings.paths.logs_dir / "runs"
        now = datetime.now().astimezone()
        cutoff = now - timedelta(days=days)
        payloads: list[dict[str, Any]] = []

        for path in sorted(run_log_dir.rglob("*.json")):
            payload = read_json(path, {})
            completed_at = payload.get("completed_at")
            if not completed_at:
                continue
            try:
                completed_at_dt = datetime.fromisoformat(completed_at)
            except ValueError:
                continue
            if completed_at_dt.tzinfo is None:
                completed_at_dt = completed_at_dt.replace(tzinfo=now.tzinfo)
            if completed_at_dt >= cutoff:
                payloads.append(payload)
        return payloads

    def _ollama_host(self) -> str:
        """读取模型服务地址。"""

        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def _update_source_records_after_dedupe(
        self,
        source_records: list[SourceRunRecord],
        deduped_items: list[ProcessedItem],
        failed_items: list[FailedItemRecord] | None = None,
    ) -> None:
        """把去重后的笔记输出和数量回写到来源记录。"""

        deduped_by_source: dict[str, list[ProcessedItem]] = {}
        for item in deduped_items:
            deduped_by_source.setdefault(item.source, []).append(item)

        failed_by_source: dict[str, list[FailedItemRecord]] = {}
        for item in failed_items or []:
            failed_by_source.setdefault(item.source, []).append(item)

        for record in source_records:
            source_items = deduped_by_source.get(record.source, [])
            record.stage_stats["deduped"] = len(source_items)
            record.note_paths = [item.note_path for item in source_items if item.note_path]
            record.stage_stats["exported"] = len(record.note_paths)
            if failed_by_source.get(record.source):
                record.stage_stats["failed"] = record.stage_stats.get("failed", 0) + len(
                    failed_by_source[record.source]
                )
                record.errors.extend(item.error for item in failed_by_source[record.source])
