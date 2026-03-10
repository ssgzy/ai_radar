"""失败条目的数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FailedItemRecord:
    """记录某个阶段失败的条目或任务。"""

    run_id: str
    stage: str
    source: str
    error: str
    title: str | None = None
    item_id: str | None = None
    url: str | None = None
    created_at: str | None = None
    prompt_path: str | None = None
    response_path: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """把失败记录转换成可序列化字典。"""

        return {
            "run_id": self.run_id,
            "stage": self.stage,
            "source": self.source,
            "error": self.error,
            "title": self.title,
            "item_id": self.item_id,
            "url": self.url,
            "created_at": self.created_at,
            "prompt_path": self.prompt_path,
            "response_path": self.response_path,
            "extra": self.extra,
        }
