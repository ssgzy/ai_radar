"""命令行参数解析入口。"""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.panel import Panel

from src.main import run_pipeline
from src.utils.logger import get_console, setup_logging


def run_cli(default_mode: str = "standard") -> None:
    """解析命令行参数并执行 AI Radar。"""

    parser = argparse.ArgumentParser(description="本地运行的 AI Radar")
    parser.add_argument(
        "--sources",
        nargs="*",
        choices=["arxiv", "github", "rss", "hackernews", "news"],
        help="指定本次运行的来源，默认使用配置文件中的全部启用来源",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        help="覆盖配置文件中的每个来源抓取数量",
    )
    parser.add_argument(
        "--mode",
        default=default_mode,
        choices=["standard", "manual", "once", "scheduler"],
        help="声明本次运行模式",
    )
    args = parser.parse_args()
    run_mode = "scheduler" if args.mode == "standard" else args.mode

    console = get_console()
    setup_logging(log_dir=Path(__file__).resolve().parent.parent / "logs")

    summary = run_pipeline(
        requested_sources=args.sources,
        max_items_override=args.max_items,
        run_mode=run_mode,
    )

    console.print(
        Panel.fit(
            f"运行 ID：{summary.run_id}\n模式：{summary.run_mode}\n处理条目：{summary.total_processed}\n质量保留：{summary.total_kept}\n质量过滤：{summary.filtered_items_count}\n去重后条目：{summary.total_deduped}\n失败条目：{summary.failed_items_count}\n耗时：{summary.duration_seconds:.1f} 秒\n日报：{summary.daily_brief_path or '无'}\n主题看板：{summary.topic_dashboard_path or '无'}\n周报：{summary.weekly_brief_path or '无'}",
            title="CLI 摘要",
        )
    )
