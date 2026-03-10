"""处理后条目的数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProcessedItem:
    """表示经过本地模型处理后的条目。"""

    source: str
    item_id: str
    title: str
    url: str
    published_at: str | None
    authors: list[str] = field(default_factory=list)
    raw_content: str = ""
    content_overview_cn: str = ""
    problem_cn: str = ""
    why_it_matters_cn: str = ""
    why_follow_cn: str = ""
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    quote_cn: str = ""
    score_breakdown: dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    priority_level: str = "未评级"
    recommendation_cn: str = ""
    score_reason_cn: str = ""
    model_name: str = ""
    quality_decision: str = "keep"
    quality_reason_cn: str = ""
    topic_name: str = ""
    note_path: str | None = None
    prompt_path: str | None = None
    response_path: str | None = None
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
            "raw_content": self.raw_content,
            "content_overview_cn": self.content_overview_cn,
            "problem_cn": self.problem_cn,
            "why_it_matters_cn": self.why_it_matters_cn,
            "why_follow_cn": self.why_follow_cn,
            "keywords": self.keywords,
            "tags": self.tags,
            "quote_cn": self.quote_cn,
            "score_breakdown": self.score_breakdown,
            "total_score": self.total_score,
            "priority_level": self.priority_level,
            "recommendation_cn": self.recommendation_cn,
            "score_reason_cn": self.score_reason_cn,
            "model_name": self.model_name,
            "quality_decision": self.quality_decision,
            "quality_reason_cn": self.quality_reason_cn,
            "topic_name": self.topic_name,
            "note_path": self.note_path,
            "prompt_path": self.prompt_path,
            "response_path": self.response_path,
            "extra": self.extra,
        }
