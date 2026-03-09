"""时间格式和时间戳工具。"""

from __future__ import annotations

from datetime import datetime


def now_local_iso() -> str:
    """返回当前本地时间的 ISO 字符串。"""

    return datetime.now().astimezone().isoformat(timespec="seconds")


def timestamp_slug() -> str:
    """返回适合文件名使用的时间戳。"""

    return datetime.now().strftime("%Y%m%d_%H%M%S")


def date_slug() -> str:
    """返回日期字符串。"""

    return datetime.now().strftime("%Y-%m-%d")
