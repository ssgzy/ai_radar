"""cron 调度配置生成。"""

from __future__ import annotations

from pathlib import Path


def build_cron_entry(project_root: Path, hour: int = 9, minute: int = 0) -> str:
    """生成适用于当前项目的 cron 配置行。"""

    script_path = project_root / "scripts" / "run_scheduler_once.sh"
    log_path = project_root / "logs" / "scheduler_cron.log"
    return f"{minute} {hour} * * * cd '{project_root}' && '{script_path}' >> '{log_path}' 2>&1"
