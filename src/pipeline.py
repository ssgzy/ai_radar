"""AI Radar 核心运行管线。"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel

from config.settings import AppSettings
from src.agents import HeuristicScorer, KeywordTagger, LocalOllamaSummarizer
from src.collectors import ArxivCollector, GitHubCollector
from src.exporters import JsonExporter, ObsidianExporter
from src.models import ProcessedItem, SourceRunRecord
from src.utils.file_ops import read_json, write_json
from src.utils.time_utils import date_slug, now_local_iso, timestamp_slug


@dataclass(slots=True)
class RunSummary:
    """保存一次完整运行的摘要信息。"""

    run_id: str
    run_mode: str
    source_records: list[SourceRunRecord]
    total_processed: int
    merged_path: str | None
    scored_path: str | None
    daily_brief_path: str | None
    duration_seconds: float


class AIRadarPipeline:
    """串联采集、总结、导出和状态保存。"""

    def __init__(
        self,
        settings: AppSettings,
        console: Console,
        requested_sources: list[str] | None = None,
        max_items_override: int | None = None,
        run_mode: str = "standard",
    ) -> None:
        self.settings = settings
        self.console = console
        self.logger = logging.getLogger("app")
        self.requested_sources = requested_sources
        self.max_items_override = max_items_override
        self.run_mode = run_mode
        self.run_id = timestamp_slug()
        self.json_exporter = JsonExporter(
            raw_root=settings.paths.raw_dir,
            processed_root=settings.paths.processed_dir,
        )
        self.obsidian_exporter = ObsidianExporter(settings.paths.obsidian_output_dir)
        self.tagger = KeywordTagger(settings.scoring.get("tagging", {}))
        self.scorer = HeuristicScorer(settings.scoring.get("scoring", {}))
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
        }

    def run(self) -> RunSummary:
        """执行完整 V2 流程。"""

        run_started_monotonic = time.monotonic()
        run_started_at = now_local_iso()
        dashboard_note_name = f"AI Radar 日报 - {date_slug()} - {self.run_id}"
        all_processed_items: list[ProcessedItem] = []
        source_records: list[SourceRunRecord] = []
        self.logger.info("运行开始 | run_id=%s | mode=%s", self.run_id, self.run_mode)

        self.console.print(
            Panel.fit(
                f"运行模式：{self.run_mode}\n运行 ID：{self.run_id}",
                title="AI Radar V2",
            )
        )

        for source_name in self._enabled_sources():
            source_started_monotonic = time.monotonic()
            source_started_at = now_local_iso()
            collector = self.collector_registry[source_name](
                source_config=self.settings.sources["sources"][source_name],
                console=self.console,
            )
            self.logger.info("开始处理来源 | source=%s", source_name)

            raw_items = collector.collect(max_items=self.max_items_override)
            raw_path = self.json_exporter.export_raw(source=source_name, items=raw_items, run_id=self.run_id)

            if not raw_items:
                source_records.append(
                    SourceRunRecord(
                        source=source_name,
                        raw_count=0,
                        processed_count=0,
                        raw_path=str(raw_path),
                        started_at=source_started_at,
                        completed_at=now_local_iso(),
                        duration_seconds=round(time.monotonic() - source_started_monotonic, 2),
                        stage_stats={"collected": 0, "summarized": 0, "tagged": 0, "scored": 0, "exported": 0},
                        errors=["没有采集到条目"],
                    )
                )
                continue

            processed_items = self.summarizer.summarize_items(items=raw_items, run_id=self.run_id)
            processed_items = self.tagger.tag_items(processed_items)
            processed_items = self.scorer.score_items(processed_items)
            processed_path = self.json_exporter.export_processed(
                source=source_name,
                items=processed_items,
                run_id=self.run_id,
            )
            note_paths = self.obsidian_exporter.export_items(
                items=processed_items,
                dashboard_note_name=dashboard_note_name,
            )

            all_processed_items.extend(processed_items)
            source_records.append(
                SourceRunRecord(
                    source=source_name,
                    raw_count=len(raw_items),
                    processed_count=len(processed_items),
                    raw_path=str(raw_path),
                    processed_path=str(processed_path),
                    started_at=source_started_at,
                    completed_at=now_local_iso(),
                    duration_seconds=round(time.monotonic() - source_started_monotonic, 2),
                    stage_stats={
                        "collected": len(raw_items),
                        "summarized": len(processed_items),
                        "tagged": len(processed_items),
                        "scored": len(processed_items),
                        "exported": len(note_paths),
                    },
                    note_paths=note_paths,
                )
            )

            self.console.print(
                f"[green]来源完成[/green] {source_name} | raw={len(raw_items)} | processed={len(processed_items)}"
            )
            self.logger.info(
                "来源完成 | source=%s | raw=%s | processed=%s",
                source_name,
                len(raw_items),
                len(processed_items),
            )

        merged_path = None
        scored_path = None
        if all_processed_items:
            merged_path = str(
                self.json_exporter.export_merged(items=all_processed_items, run_id=self.run_id)
            )
            scored_path = str(
                self.json_exporter.export_scored(items=all_processed_items, run_id=self.run_id)
            )

        daily_brief_path = str(
            self.obsidian_exporter.export_daily_brief(
                records=source_records,
                items=all_processed_items,
                note_name=dashboard_note_name,
                run_id=self.run_id,
            )
        )

        total_duration_seconds = round(time.monotonic() - run_started_monotonic, 2)
        self._write_state(
            source_records=source_records,
            all_processed_items=all_processed_items,
            started_at=run_started_at,
            duration_seconds=total_duration_seconds,
            merged_path=merged_path,
            scored_path=scored_path,
            daily_brief_path=daily_brief_path,
        )

        self.console.print(
            Panel.fit(
                f"处理条目：{len(all_processed_items)}\n运行耗时：{total_duration_seconds:.1f} 秒\nMerged JSON：{merged_path or '无'}\nScored JSON：{scored_path or '无'}\n日报：{daily_brief_path}",
                title="运行完成",
            )
        )
        self.logger.info(
            "运行完成 | run_id=%s | total_processed=%s | duration=%.2f | merged=%s | scored=%s | brief=%s",
            self.run_id,
            len(all_processed_items),
            total_duration_seconds,
            merged_path,
            scored_path,
            daily_brief_path,
        )

        return RunSummary(
            run_id=self.run_id,
            run_mode=self.run_mode,
            source_records=source_records,
            total_processed=len(all_processed_items),
            merged_path=merged_path,
            scored_path=scored_path,
            daily_brief_path=daily_brief_path,
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

    def _write_state(
        self,
        source_records: list[SourceRunRecord],
        all_processed_items: list[ProcessedItem],
        started_at: str,
        duration_seconds: float,
        merged_path: str | None,
        scored_path: str | None,
        daily_brief_path: str | None,
    ) -> None:
        """写入运行状态和已见集合。"""

        state_dir = self.settings.paths.state_dir
        run_log_dir = self.settings.paths.logs_dir / "runs"
        last_run_payload = {
            "run_id": self.run_id,
            "run_mode": self.run_mode,
            "started_at": started_at,
            "completed_at": now_local_iso(),
            "duration_seconds": duration_seconds,
            "sources": [record.to_dict() for record in source_records],
            "total_processed": len(all_processed_items),
            "merged_path": merged_path,
            "scored_path": scored_path,
            "daily_brief_path": daily_brief_path,
            "top_items": [
                {
                    "title": item.title,
                    "source": item.source,
                    "total_score": item.total_score,
                    "priority_level": item.priority_level,
                    "note_path": item.note_path,
                }
                for item in sorted(all_processed_items, key=lambda item: item.total_score, reverse=True)[:5]
            ],
        }
        write_json(state_dir / "last_run.json", last_run_payload)
        write_json(run_log_dir / f"{self.run_id}.json", last_run_payload)

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

    def _ollama_host(self) -> str:
        """读取模型服务地址。"""

        return os.getenv("OLLAMA_HOST", "http://localhost:11434")
