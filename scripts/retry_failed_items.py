"""重试 failed_items 中可回放的条目。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import load_settings
from src.recovery import FailedItemReplayer
from src.utils.logger import get_console, setup_logging


def main() -> None:
    """读取失败记录并重试可恢复条目。"""

    parser = argparse.ArgumentParser(description="重试 AI Radar 的 failed_items")
    parser.add_argument("--failed-file", required=True, help="failed_items JSON 文件路径")
    parser.add_argument("--max-items", type=int, help="限制重试条目数量")
    args = parser.parse_args()

    settings = load_settings()
    console = get_console()
    setup_logging(log_dir=settings.paths.logs_dir)
    replayer = FailedItemReplayer(settings=settings, console=console)
    summary = replayer.replay_failed_file(
        failed_file=Path(args.failed_file).expanduser().resolve(),
        max_items=args.max_items,
    )

    console.print(
        "\n".join(
            [
                "失败回放完成",
                f"运行 ID：{summary.run_id}",
                f"重试条目：{summary.retried_count}",
                f"恢复成功：{summary.recovered_count}",
                f"仍失败：{summary.failed_count}",
                f"跳过：{summary.skipped_count}",
                f"日报：{summary.dashboard_path or '无'}",
                f"失败记录：{summary.failed_items_path or '无'}",
            ]
        )
    )


if __name__ == "__main__":
    main()
