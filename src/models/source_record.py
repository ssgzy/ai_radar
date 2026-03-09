"""每个来源一次运行的结果记录。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceRunRecord:
    """描述某个来源在本次运行中的产出。"""

    source: str
    raw_count: int
    processed_count: int
    raw_path: str | None = None
    processed_path: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    stage_stats: dict[str, Any] = field(default_factory=dict)
    note_paths: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """把结果记录转换成字典。"""

        return {
            "source": self.source,
            "raw_count": self.raw_count,
            "processed_count": self.processed_count,
            "raw_path": self.raw_path,
            "processed_path": self.processed_path,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "stage_stats": self.stage_stats,
            "note_paths": self.note_paths,
            "errors": self.errors,
            "extra": self.extra,
        }
