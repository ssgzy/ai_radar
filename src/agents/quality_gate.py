"""基于规则的来源质量过滤器。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.models import ProcessedItem
from src.utils.text_utils import normalize_whitespace


@dataclass(slots=True)
class QualityDecision:
    """保存单条内容的质量过滤决策。"""

    source: str
    item_id: str
    title: str
    keep: bool
    topic_name: str
    total_score: float
    adjusted_score: float
    focus_tag_hits: list[str]
    strong_keyword_hits: list[str]
    medium_keyword_hits: list[str]
    blocked_hits: list[str]
    reason_cn: str

    def to_dict(self) -> dict[str, Any]:
        """把过滤决策转换成字典。"""

        return {
            "source": self.source,
            "item_id": self.item_id,
            "title": self.title,
            "keep": self.keep,
            "topic_name": self.topic_name,
            "total_score": self.total_score,
            "adjusted_score": self.adjusted_score,
            "focus_tag_hits": self.focus_tag_hits,
            "strong_keyword_hits": self.strong_keyword_hits,
            "medium_keyword_hits": self.medium_keyword_hits,
            "blocked_hits": self.blocked_hits,
            "reason_cn": self.reason_cn,
        }


@dataclass(slots=True)
class QualityGateResult:
    """保存质量过滤后的整体结果。"""

    kept_items: list[ProcessedItem]
    filtered_items: list[ProcessedItem]
    decisions: list[QualityDecision]


class SourceQualityGate:
    """根据来源阈值、主题标签和关键词过滤低价值条目。"""

    def __init__(self, gate_config: dict[str, Any]) -> None:
        self.logger = logging.getLogger("quality_gate")
        self.gate_config = gate_config or {}
        self.keep_all_sources = set(self.gate_config.get("keep_all_sources", ["arxiv", "github"]))
        self.source_min_scores = self.gate_config.get("source_min_scores", {})
        self.preferred_topic_tags = self.gate_config.get("preferred_topic_tags", [])
        self.blocked_title_keywords = self.gate_config.get("blocked_title_keywords", [])
        self.blocked_body_keywords = self.gate_config.get("blocked_body_keywords", [])
        self.focus_keywords = self.gate_config.get("focus_keywords", {})
        self.minimum_focus_signals = self.gate_config.get("minimum_focus_signals", {})

    def filter_items(self, items: list[ProcessedItem]) -> QualityGateResult:
        """批量过滤条目，并保留决策说明。"""

        kept_items: list[ProcessedItem] = []
        filtered_items: list[ProcessedItem] = []
        decisions: list[QualityDecision] = []

        for item in items:
            decision = self._evaluate_item(item)
            decisions.append(decision)
            if decision.keep:
                kept_items.append(item)
            else:
                filtered_items.append(item)

            self.logger.info(
                "质量过滤 | source=%s | title=%s | keep=%s | adjusted=%.1f | reason=%s",
                item.source,
                item.title,
                decision.keep,
                decision.adjusted_score,
                decision.reason_cn,
            )

        return QualityGateResult(
            kept_items=kept_items,
            filtered_items=filtered_items,
            decisions=decisions,
        )

    def _evaluate_item(self, item: ProcessedItem) -> QualityDecision:
        """计算单条内容是否应进入后续聚合与导出。"""

        if item.source in self.keep_all_sources:
            item.quality_decision = "keep"
            item.quality_reason_cn = "核心来源默认保留。"
            item.extra["quality_gate"] = {
                "keep": True,
                "adjusted_score": item.total_score,
                "reason_cn": item.quality_reason_cn,
                "focus_tag_hits": [],
                "strong_keyword_hits": [],
                "medium_keyword_hits": [],
                "blocked_hits": [],
            }
            return QualityDecision(
                source=item.source,
                item_id=item.item_id,
                title=item.title,
                keep=True,
                topic_name=item.topic_name,
                total_score=item.total_score,
                adjusted_score=item.total_score,
                focus_tag_hits=[],
                strong_keyword_hits=[],
                medium_keyword_hits=[],
                blocked_hits=[],
                reason_cn=item.quality_reason_cn,
            )

        combined_text = self._combined_text(item)
        normalized_title = normalize_whitespace(item.title.lower())
        normalized_body = normalize_whitespace(
            " ".join([item.raw_content, item.content_overview_cn, item.why_it_matters_cn]).lower()
        )

        focus_tag_hits = [tag for tag in item.tags if tag in self.preferred_topic_tags]
        strong_keyword_hits = self._matched_keywords(combined_text, self.focus_keywords.get("strong", []))
        medium_keyword_hits = self._matched_keywords(combined_text, self.focus_keywords.get("medium", []))
        blocked_hits = self._matched_keywords(normalized_title, self.blocked_title_keywords)
        blocked_hits.extend(self._matched_keywords(normalized_body, self.blocked_body_keywords))

        adjusted_score = item.total_score
        adjusted_score += min(len(focus_tag_hits) * 0.7, 2.1)
        adjusted_score += min(len(strong_keyword_hits) * 0.5, 1.5)
        adjusted_score += min(len(medium_keyword_hits) * 0.2, 0.6)
        adjusted_score -= min(len(set(blocked_hits)) * 1.5, 3.0)
        adjusted_score = round(min(max(adjusted_score, 0.0), 10.0), 1)

        minimum_focus = int(self.minimum_focus_signals.get(item.source, 0))
        threshold = float(self.source_min_scores.get(item.source, 0.0))
        focus_signal_count = len(focus_tag_hits) + len(strong_keyword_hits)

        keep = True
        reasons: list[str] = []
        if blocked_hits and focus_signal_count == 0:
            keep = False
            reasons.append(f"命中过滤词：{', '.join(sorted(set(blocked_hits)))}")
        elif adjusted_score < threshold and focus_signal_count < minimum_focus:
            keep = False
            reasons.append(f"调节后分数 {adjusted_score:.1f} 低于阈值 {threshold:.1f}")
            reasons.append("主题信号不足")
        else:
            reasons.append(f"调节后分数 {adjusted_score:.1f} 达到阈值 {threshold:.1f}")
            if focus_tag_hits:
                reasons.append(f"命中主题标签：{', '.join(focus_tag_hits[:3])}")
            if strong_keyword_hits:
                reasons.append(f"命中强信号：{', '.join(strong_keyword_hits[:3])}")

        reason_cn = "；".join(reasons) if reasons else "通过默认规则保留。"
        item.quality_decision = "keep" if keep else "filter"
        item.quality_reason_cn = reason_cn
        item.extra["quality_gate"] = {
            "keep": keep,
            "adjusted_score": adjusted_score,
            "reason_cn": reason_cn,
            "focus_tag_hits": focus_tag_hits,
            "strong_keyword_hits": strong_keyword_hits,
            "medium_keyword_hits": medium_keyword_hits,
            "blocked_hits": sorted(set(blocked_hits)),
        }

        return QualityDecision(
            source=item.source,
            item_id=item.item_id,
            title=item.title,
            keep=keep,
            topic_name=item.topic_name,
            total_score=item.total_score,
            adjusted_score=adjusted_score,
            focus_tag_hits=focus_tag_hits,
            strong_keyword_hits=strong_keyword_hits,
            medium_keyword_hits=medium_keyword_hits,
            blocked_hits=sorted(set(blocked_hits)),
            reason_cn=reason_cn,
        )

    def _combined_text(self, item: ProcessedItem) -> str:
        """拼接过滤所需文本。"""

        return normalize_whitespace(
            " ".join(
                [
                    item.title,
                    item.raw_content,
                    item.content_overview_cn,
                    item.problem_cn,
                    item.why_it_matters_cn,
                    item.why_follow_cn,
                    " ".join(item.tags),
                    " ".join(item.keywords),
                ]
            ).lower()
        )

    def _matched_keywords(self, text: str, keywords: list[str]) -> list[str]:
        """返回命中的关键词列表。"""

        normalized_text = normalize_whitespace(text.lower())
        return [
            normalize_whitespace(keyword)
            for keyword in keywords
            if normalize_whitespace(keyword.lower()) and normalize_whitespace(keyword.lower()) in normalized_text
        ]
