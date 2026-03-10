"""生成 cron 与 launchd 的示例配置。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import load_settings
from src.schedulers import build_cron_entry, build_launchd_plist
from src.utils.file_ops import ensure_dir, write_text


def main() -> None:
    """生成调度示例文件。"""

    parser = argparse.ArgumentParser(description="生成 AI Radar 调度示例配置")
    parser.add_argument("--hour", type=int, default=9, help="每天执行的小时数")
    parser.add_argument("--minute", type=int, default=0, help="每天执行的分钟数")
    parser.add_argument(
        "--label",
        default="local.ai_radar.scheduler",
        help="launchd 使用的任务标签",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="写入 launchd 配置中的 Python 可执行文件路径",
    )
    args = parser.parse_args()

    settings = load_settings()
    export_dir = ensure_dir(settings.paths.outputs_dir / "exports" / "markdown" / "scheduling")

    cron_content = build_cron_entry(
        project_root=settings.paths.project_root,
        hour=args.hour,
        minute=args.minute,
    )
    launchd_content = build_launchd_plist(
        label=args.label,
        project_root=settings.paths.project_root,
        python_executable=args.python,
        hour=args.hour,
        minute=args.minute,
    )

    cron_path = write_text(export_dir / "cron.example.txt", cron_content + "\n")
    launchd_path = write_text(export_dir / "ai_radar.launchd.plist", launchd_content)

    print(f"cron 示例：{cron_path}")
    print(f"launchd 示例：{launchd_path}")


if __name__ == "__main__":
    main()
