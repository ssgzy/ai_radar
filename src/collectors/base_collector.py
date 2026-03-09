"""采集器抽象基类。"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from rich.console import Console

from src.models import RawItem


class BaseCollector(ABC):
    """定义所有 collector 的统一接口。"""

    source_name: str = "base"

    def __init__(self, source_config: dict[str, Any], console: Console) -> None:
        self.source_config = source_config
        self.console = console
        self.logger = logging.getLogger("collector")

    @abstractmethod
    def collect(self, max_items: int | None = None) -> list[RawItem]:
        """抓取并返回原始条目。"""
