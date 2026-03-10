"""验证导出器会按日期和按周归档。"""

from pathlib import Path

from src.agents.quality_gate import QualityDecision
from src.exporters import DashboardExporter, DebugExporter, JsonExporter, ObsidianExporter, ReportExporter
from src.models import FailedItemRecord, ProcessedItem, RawItem, SourceRunRecord


def test_json_exporter_writes_daily_archive_paths(tmp_path):
    """原始和处理结果应该落到按日期分层的目录。"""

    exporter = JsonExporter(raw_root=tmp_path / "raw", processed_root=tmp_path / "processed")
    raw_item = RawItem(
        source="rss",
        item_id="item-1",
        title="示例 RSS",
        url="https://example.com/rss",
        published_at="2026-03-10T09:00:00+08:00",
        content="示例内容",
    )
    processed_item = ProcessedItem(
        source="rss",
        item_id="item-1",
        title="示例 RSS",
        url="https://example.com/rss",
        published_at="2026-03-10T09:00:00+08:00",
    )

    raw_path = exporter.export_raw("rss", [raw_item], "run-1", archive_date="2026-03-10")
    processed_path = exporter.export_processed("rss", [processed_item], "run-1", archive_date="2026-03-10")
    merged_path = exporter.export_merged([processed_item], "run-1", archive_date="2026-03-10")
    deduped_path = exporter.export_deduped([processed_item], "run-1", archive_date="2026-03-10")
    duplicate_path = exporter.export_duplicate_report([], "run-1", archive_date="2026-03-10")

    assert raw_path == tmp_path / "raw" / "rss" / "2026-03-10" / "rss_run-1.json"
    assert processed_path == tmp_path / "processed" / "rss" / "2026-03-10" / "rss_run-1.json"
    assert merged_path == tmp_path / "processed" / "merged" / "2026-03-10" / "merged_run-1.json"
    assert deduped_path == tmp_path / "processed" / "deduped" / "2026-03-10" / "deduped_run-1.json"
    assert duplicate_path == tmp_path / "processed" / "deduped" / "2026-03-10" / "duplicates_run-1.json"


def test_obsidian_exporter_writes_daily_and_weekly_archive_paths(tmp_path):
    """日报和周报应该分别写入日期目录和周目录。"""

    exporter = ObsidianExporter(tmp_path / "obsidian")
    item = ProcessedItem(
        source="news",
        item_id="news-1",
        title="示例新闻",
        url="https://example.com/news",
        published_at="2026-03-10T10:00:00+08:00",
        total_score=8.5,
        priority_level="重点关注",
        tags=["Agent"],
        why_it_matters_cn="这条新闻说明代理工作流正在继续落地。",
        note_path=str(tmp_path / "obsidian" / "inbox" / "资讯 - 示例新闻.md"),
    )
    record = SourceRunRecord(
        source="news",
        raw_count=1,
        processed_count=1,
        stage_stats={"deduped": 1, "failed": 0},
        duration_seconds=1.2,
    )

    daily_path = exporter.export_daily_brief(
        records=[record],
        items=[item],
        note_name="AI Radar 日报 - 2026-03-10 - run-1",
        run_id="run-1",
        total_processed=1,
        duplicate_count=0,
        archive_date="2026-03-10",
    )
    weekly_path, _ = exporter.export_weekly_brief(
        run_payloads=[
            {
                "run_id": "run-1",
                "run_mode": "manual",
                "completed_at": "2026-03-10T10:30:00+08:00",
                "total_processed": 1,
                "total_deduped": 1,
                "failed_items_count": 0,
                "sources": [record.to_dict()],
                "top_items": [item.to_dict()],
            }
        ],
        note_name="AI Radar 周报 - 2026-W11",
        archive_week="2026-W11",
    )

    assert daily_path == tmp_path / "obsidian" / "dashboards" / "daily" / "2026-03-10" / "AI Radar 日报 - 2026-03-10 - run-1.md"
    assert weekly_path == tmp_path / "obsidian" / "dashboards" / "weekly" / "2026-W11" / "AI Radar 周报 - 2026-W11.md"


def test_debug_and_report_exporters_use_archive_folders(tmp_path):
    """调试输出和周报副本也应该进入归档目录。"""

    debug_exporter = DebugExporter(tmp_path / "debug")
    report_exporter = ReportExporter(tmp_path / "reports")
    dashboard_exporter = DashboardExporter(tmp_path / "obsidian")

    failed_path = debug_exporter.export_failed_items(
        run_id="run-1",
        failures=[FailedItemRecord(run_id="run-1", stage="summarize", source="rss", error="timeout")],
        archive_date="2026-03-10",
    )
    quality_path = debug_exporter.export_quality_report(
        run_id="run-1",
        decisions=[
            QualityDecision(
                source="rss",
                item_id="item-1",
                title="示例",
                keep=True,
                topic_name="Agent",
                total_score=6.1,
                adjusted_score=6.8,
                focus_tag_hits=["Agent"],
                strong_keyword_hits=["agent"],
                medium_keyword_hits=[],
                blocked_hits=[],
                reason_cn="通过",
            )
        ],
        archive_date="2026-03-10",
    )
    report_path = report_exporter.export_weekly_report(
        note_name="AI Radar 周报 - 2026-W11",
        content="# 周报",
        archive_week="2026-W11",
    )
    dashboard_path = dashboard_exporter.export_topic_dashboard(
        clusters=[],
        records=[],
        note_name="AI Radar 主题看板 - 2026-03-10 - run-1",
        run_id="run-1",
        filtered_count=0,
        quality_report_path=str(quality_path),
        daily_brief_note_name="AI Radar 日报 - 2026-03-10 - run-1",
        archive_date="2026-03-10",
    )

    assert failed_path == tmp_path / "debug" / "failed_items" / "2026-03-10" / "failed_items_run-1.json"
    assert quality_path == tmp_path / "debug" / "quality_gate" / "2026-03-10" / "quality_report_run-1.json"
    assert report_path == tmp_path / "reports" / "weekly" / "2026-W11" / "AI Radar 周报 - 2026-W11.md"
    assert dashboard_path == tmp_path / "obsidian" / "dashboards" / "daily" / "2026-03-10" / "AI Radar 主题看板 - 2026-03-10 - run-1.md"
    assert Path(report_path).read_text(encoding="utf-8") == "# 周报"
