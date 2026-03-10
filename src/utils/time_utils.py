"""时间格式和时间戳工具。"""

from __future__ import annotations

from datetime import datetime


def now_local_iso() -> str:
    """返回当前本地时间的 ISO 字符串。"""

    return datetime.now().astimezone().isoformat(timespec="seconds")


def timestamp_slug() -> str:
    """返回适合文件名使用的时间戳。"""

    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def date_slug() -> str:
    """返回日期字符串。"""

    return datetime.now().strftime("%Y-%m-%d")


def week_slug() -> str:
    """返回 ISO 周字符串。"""

    iso_year, iso_week, _ = datetime.now().isocalendar()
    return f"{iso_year}-W{iso_week:02d}"
