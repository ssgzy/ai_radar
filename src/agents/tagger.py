"""基于关键词规则的标签器。"""

from __future__ import annotations

import logging
from typing import Any

from src.models import ProcessedItem


class KeywordTagger:
    """根据配置中的关键词给条目打标签。"""

    def __init__(self, tagging_config: dict[str, Any]) -> None:
        self.logger = logging.getLogger("tagger")
        self.tagging_config = tagging_config or {}

    def tag_items(self, items: list[ProcessedItem]) -> list[ProcessedItem]:
        """批量给条目打标签。"""

        for item in items:
            item.tags = self._build_tags(item)
            self.logger.info("标签完成 | source=%s | title=%s | tags=%s", item.source, item.title, item.tags)
        return items

    def _build_tags(self, item: ProcessedItem) -> list[str]:
        """为单条内容生成标签。"""

        combined_text = " ".join(
            [
                item.title,
                item.raw_content,
                item.content_overview_cn,
                item.problem_cn,
                item.why_it_matters_cn,
                " ".join(item.keywords),
            ]
        ).lower()

        tags: list[str] = []
        source_tag = self.tagging_config.get("source_tags", {}).get(item.source)
        if source_tag:
            tags.append(source_tag)

        for tag_name, keywords in self.tagging_config.get("topics", {}).items():
            if any(keyword.lower() in combined_text for keyword in keywords):
                tags.append(tag_name)

        if item.source == "github" and int(item.extra.get("stars", 0) or 0) >= 20:
            tags.append("高星信号")
        if item.source == "arxiv":
            tags.append("研究跟踪")

        deduped_tags: list[str] = []
        for tag in tags:
            if tag and tag not in deduped_tags:
                deduped_tags.append(tag)

        return deduped_tags or ["待分类"]
