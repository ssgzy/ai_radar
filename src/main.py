"""AI Radar 程序主入口。"""

from __future__ import annotations

from config.settings import load_settings
from src.pipeline import AIRadarPipeline, RunSummary
from src.schedulers import RuntimeTaskManager, TaskLockError
from src.utils.logger import get_console


def run_pipeline(
    requested_sources: list[str] | None = None,
    max_items_override: int | None = None,
    run_mode: str = "standard",
) -> RunSummary:
    """加载配置后执行主管线。"""

    settings = load_settings()
    console = get_console()
    effective_mode = "scheduler" if run_mode == "standard" else run_mode
    pipeline = AIRadarPipeline(
        settings=settings,
        console=console,
        requested_sources=requested_sources,
        max_items_override=max_items_override,
        run_mode=effective_mode,
    )
    if effective_mode != "scheduler":
        return pipeline.run()

    task_manager = RuntimeTaskManager(settings.paths.project_root / ".runtime")
    try:
        with task_manager.guard(task_name="ai_radar_scheduler", run_id=pipeline.run_id, run_mode=effective_mode) as payload:
            pipeline.runtime_context = payload
            return pipeline.run()
    except TaskLockError as error:
        console.print(f"[red]调度运行被拒绝[/red] {error}")
        raise
