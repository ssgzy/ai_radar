"""主题聚合结果的数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TopicCluster:
    """表示一次运行中聚合出的主题分组。"""

    topic_name: str
    item_count: int
    avg_score: float
    max_score: float
    source_counts: dict[str, int] = field(default_factory=dict)
    top_keywords: list[str] = field(default_factory=list)
    summary_cn: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """把主题分组转换成可序列化字典。"""

        return {
            "topic_name": self.topic_name,
            "item_count": self.item_count,
            "avg_score": self.avg_score,
            "max_score": self.max_score,
            "source_counts": self.source_counts,
            "top_keywords": self.top_keywords,
            "summary_cn": self.summary_cn,
            "items": self.items,
        }
