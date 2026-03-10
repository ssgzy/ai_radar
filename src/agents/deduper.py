"""启发式去重器。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlparse, urlunparse

from src.models import ProcessedItem
from src.utils.text_utils import normalize_whitespace


@dataclass(slots=True)
class DeduplicationResult:
    """保存一次去重结果。"""

    unique_items: list[ProcessedItem]
    duplicates: list[dict[str, Any]] = field(default_factory=list)


class HeuristicDeduper:
    """根据 URL、标题和相似度做去重。"""

    SOURCE_PRIORITY = {
        "arxiv": 5,
        "github": 4,
        "news": 3,
        "rss": 2,
        "hackernews": 1,
    }

    def __init__(self, title_similarity_threshold: float = 0.93) -> None:
        self.logger = logging.getLogger("deduper")
        self.title_similarity_threshold = title_similarity_threshold

    def dedupe_items(self, items: list[ProcessedItem]) -> DeduplicationResult:
        """对处理后条目列表去重。"""

        sorted_items = sorted(
            items,
            key=lambda item: (
                item.total_score,
                self.SOURCE_PRIORITY.get(item.source, 0),
                len(item.raw_content),
            ),
            reverse=True,
        )

        unique_items: list[ProcessedItem] = []
        duplicates: list[dict[str, Any]] = []

        for candidate in sorted_items:
            duplicated_into = self._find_duplicate_target(candidate, unique_items)
            if duplicated_into is None:
                candidate.extra.setdefault("duplicate_sources", [])
                unique_items.append(candidate)
                continue

            duplicated_into.extra.setdefault("duplicate_sources", []).append(
                {
                    "source": candidate.source,
                    "title": candidate.title,
                    "url": candidate.url,
                }
            )
            duplicate_record = {
                "duplicate_title": candidate.title,
                "duplicate_source": candidate.source,
                "duplicate_url": candidate.url,
                "kept_title": duplicated_into.title,
                "kept_source": duplicated_into.source,
                "kept_url": duplicated_into.url,
                "reason": self._duplicate_reason(candidate, duplicated_into),
            }
            duplicates.append(duplicate_record)
            self.logger.info(
                "去重命中 | duplicate=%s | kept=%s | reason=%s",
                candidate.title,
                duplicated_into.title,
                duplicate_record["reason"],
            )

        return DeduplicationResult(unique_items=unique_items, duplicates=duplicates)

    def _find_duplicate_target(
        self,
        candidate: ProcessedItem,
        unique_items: list[ProcessedItem],
    ) -> ProcessedItem | None:
        """从已保留条目中找到重复目标。"""

        for kept_item in unique_items:
            if self._is_duplicate(candidate, kept_item):
                return kept_item
        return None

    def _is_duplicate(self, item_a: ProcessedItem, item_b: ProcessedItem) -> bool:
        """判断两条内容是否重复。"""

        canonical_url_a = self._canonical_url(item_a.url)
        canonical_url_b = self._canonical_url(item_b.url)
        if canonical_url_a and canonical_url_b and canonical_url_a == canonical_url_b:
            return True

        normalized_title_a = self._normalize_title(item_a.title)
        normalized_title_b = self._normalize_title(item_b.title)
        if normalized_title_a and normalized_title_a == normalized_title_b:
            return True

        if normalized_title_a and normalized_title_b:
            similarity = SequenceMatcher(None, normalized_title_a, normalized_title_b).ratio()
            if similarity >= self.title_similarity_threshold:
                return True

        return False

    def _duplicate_reason(self, item_a: ProcessedItem, item_b: ProcessedItem) -> str:
        """返回命中的重复原因。"""

        if self._canonical_url(item_a.url) and self._canonical_url(item_a.url) == self._canonical_url(item_b.url):
            return "canonical_url"
        if self._normalize_title(item_a.title) == self._normalize_title(item_b.title):
            return "normalized_title"
        return "title_similarity"

    def _canonical_url(self, url: str | None) -> str:
        """去掉 query 和 fragment，获得稳定 URL。"""

        if not url:
            return ""

        parsed = urlparse(url)
        cleaned = parsed._replace(query="", fragment="")
        canonical = urlunparse(cleaned).rstrip("/")
        return canonical.lower()

    def _normalize_title(self, title: str | None) -> str:
        """把标题归一化，方便做去重比较。"""

        normalized = normalize_whitespace(title).lower()
        normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", normalized)
        return normalize_whitespace(normalized)
