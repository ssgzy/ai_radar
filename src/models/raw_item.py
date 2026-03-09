"""原始采集条目的数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RawItem:
    """表示来自某个来源的一条原始内容。"""

    source: str
    item_id: str
    title: str
    url: str
    published_at: str | None
    authors: list[str] = field(default_factory=list)
    content: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """把数据结构转换成可序列化字典。"""

        return {
            "source": self.source,
            "item_id": self.item_id,
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "authors": self.authors,
            "content": self.content,
            "extra": self.extra,
        }
