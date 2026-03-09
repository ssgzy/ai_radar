"""AI Radar 程序主入口。"""

from __future__ import annotations

from config.settings import load_settings
from src.pipeline import AIRadarPipeline, RunSummary
from src.utils.logger import get_console


def run_pipeline(
    requested_sources: list[str] | None = None,
    max_items_override: int | None = None,
    run_mode: str = "standard",
) -> RunSummary:
    """加载配置后执行主管线。"""

    settings = load_settings()
    console = get_console()
    pipeline = AIRadarPipeline(
        settings=settings,
        console=console,
        requested_sources=requested_sources,
        max_items_override=max_items_override,
        run_mode=run_mode,
    )
    return pipeline.run()
