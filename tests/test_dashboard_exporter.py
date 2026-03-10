"""主题看板导出器测试。"""

from src.exporters.dashboard_exporter import DashboardExporter
from src.models import SourceRunRecord, TopicCluster


def test_dashboard_exporter_writes_daily_dashboard(tmp_path):
    """主题看板应该落到按日期归档的 dashboards 目录。"""

    exporter = DashboardExporter(tmp_path / "obsidian")
    cluster = TopicCluster(
        topic_name="Agent",
        item_count=2,
        avg_score=7.5,
        max_score=8.8,
        source_counts={"github": 1, "news": 1},
        top_keywords=["agent", "workflow"],
        summary_cn="本轮 Agent 主题同时覆盖项目和资讯。",
        items=[
            {
                "title": "Agent workspace",
                "source": "github",
                "total_score": 8.8,
                "priority_level": "高优先级跟进",
                "note_path": "/tmp/项目 - Agent workspace.md",
            }
        ],
    )
    record = SourceRunRecord(
        source="github",
        raw_count=2,
        processed_count=2,
        stage_stats={"quality_kept": 1, "quality_filtered": 1},
    )

    path = exporter.export_topic_dashboard(
        clusters=[cluster],
        records=[record],
        note_name="AI Radar 主题看板 - 2026-03-10 - run-1",
        run_id="run-1",
        filtered_count=1,
        quality_report_path="/tmp/quality_report_run-1.json",
        daily_brief_note_name="AI Radar 日报 - 2026-03-10 - run-1",
        archive_date="2026-03-10",
    )

    assert path == tmp_path / "obsidian" / "dashboards" / "daily" / "2026-03-10" / "AI Radar 主题看板 - 2026-03-10 - run-1.md"
    assert "主题聚合" in path.read_text(encoding="utf-8")
