"""控制台与文件日志初始化。"""

from __future__ import annotations

import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from src.utils.file_ops import ensure_dir

_CONSOLE = Console()


def get_console() -> Console:
    """返回共享的 Rich 控制台对象。"""

    return _CONSOLE


def setup_logging(log_dir: Path) -> dict[str, logging.Logger]:
    """初始化控制台和文件日志。"""

    ensure_dir(log_dir)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=_CONSOLE, rich_tracebacks=True, show_path=False)],
        force=True,
    )

    logger_names = [
        "app",
        "collector",
        "summarizer",
        "scorer",
        "tagger",
        "quality_gate",
        "topic",
        "deduper",
        "exporter",
        "scheduler",
        "errors",
    ]
    loggers: dict[str, logging.Logger] = {}

    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = True

        # 每个命名 logger 都保留单独文件，便于后续追踪问题。
        file_handler = logging.FileHandler(log_dir / f"{logger_name}.log", encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
        )

        logger.handlers = [file_handler]
        logger.propagate = True
        loggers[logger_name] = logger

    return loggers
