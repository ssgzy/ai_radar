"""基于启发式规则的评分器。"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any

from src.models import ProcessedItem


class HeuristicScorer:
    """根据来源、时效、关键词和元信息计算分数。"""

    def __init__(self, scoring_config: dict[str, Any]) -> None:
        self.logger = logging.getLogger("scorer")
        self.scoring_config = scoring_config or {}
        self.dimensions = self.scoring_config.get("dimensions", {})
        self.thresholds = self.scoring_config.get("thresholds", {})
        self.interest_keywords = self.scoring_config.get("interest_keywords", {})
        self.novelty_keywords = self.scoring_config.get("novelty_keywords", [])
        self.execution_keywords = self.scoring_config.get("execution_keywords", [])

    def score_items(self, items: list[ProcessedItem]) -> list[ProcessedItem]:
        """批量给条目打分。"""

        for item in items:
            breakdown = {
                "novelty": self._score_novelty(item),
                "execution_signal": self._score_execution(item),
                "personal_relevance": self._score_relevance(item),
            }
            total_score = self._weighted_total(breakdown)
            priority_level, recommendation_cn = self._priority_and_recommendation(total_score)

            item.score_breakdown = breakdown
            item.total_score = total_score
            item.priority_level = priority_level
            item.recommendation_cn = recommendation_cn
            item.score_reason_cn = self._build_reason(item, breakdown, total_score)

            self.logger.info(
                "评分完成 | source=%s | title=%s | total=%.1f | level=%s",
                item.source,
                item.title,
                total_score,
                priority_level,
            )

        return items

    def _score_novelty(self, item: ProcessedItem) -> float:
        """计算新颖性分数。"""

        text = self._combined_text(item)
        keyword_hits = sum(1 for keyword in self.novelty_keywords if keyword.lower() in text)
        score = 3.5 + min(keyword_hits * 0.8, 3.2) + self._freshness_bonus(item)

        if item.source == "arxiv":
            score += 1.0
        if "多模态" in item.tags or "Agent" in item.tags or "评测与基准" in item.tags:
            score += 0.5

        return round(min(score, 10.0), 1)

    def _score_execution(self, item: ProcessedItem) -> float:
        """计算落地信号分数。"""

        text = self._combined_text(item)
        keyword_hits = sum(1 for keyword in self.execution_keywords if keyword.lower() in text)
        score = 3.0 + min(keyword_hits * 0.6, 2.4)

        if item.source == "github":
            stars = int(item.extra.get("stars", 0) or 0)
            if stars >= 200:
                score += 4.0
            elif stars >= 50:
                score += 3.0
            elif stars >= 20:
                score += 2.0
            elif stars >= 5:
                score += 1.0
            if item.extra.get("language"):
                score += 0.6
            if item.extra.get("description"):
                score += 0.8
        else:
            if item.extra.get("pdf_url"):
                score += 0.8
            if len(item.authors) >= 3:
                score += 0.6
            if any(tag in item.tags for tag in ["评测与基准", "研究跟踪"]):
                score += 1.0
            if len(item.raw_content) >= 600:
                score += 0.8

        return round(min(score, 10.0), 1)

    def _score_relevance(self, item: ProcessedItem) -> float:
        """计算与当前项目目标的相关性。"""

        text = self._combined_text(item)
        strong_hits = sum(1 for keyword in self.interest_keywords.get("strong", []) if keyword.lower() in text)
        medium_hits = sum(1 for keyword in self.interest_keywords.get("medium", []) if keyword.lower() in text)

        score = 3.0 + min(strong_hits * 1.1, 4.4) + min(medium_hits * 0.5, 2.0)

        if item.source == "github":
            score += 0.4
        if any(tag in item.tags for tag in ["Agent", "大模型", "多模态", "本地 AI", "开发工具"]):
            score += 0.8
        if "自动化" in item.tags:
            score += 0.5

        return round(min(score, 10.0), 1)

    def _weighted_total(self, breakdown: dict[str, float]) -> float:
        """根据权重计算总分。"""

        total = 0.0
        for dimension_name, score in breakdown.items():
            weight = float(self.dimensions.get(dimension_name, {}).get("weight", 0.0))
            total += score * weight
        return round(min(total, 10.0), 1)

    def _priority_and_recommendation(self, total_score: float) -> tuple[str, str]:
        """根据总分映射优先级和动作建议。"""

        if total_score >= float(self.thresholds.get("high_priority", 8.0)):
            return "高优先级跟进", "建议放入今日重点，优先精读论文或试用项目。"
        if total_score >= float(self.thresholds.get("watchlist", 6.5)):
            return "重点关注", "建议加入观察清单，今天至少完成一次快速复盘。"
        if total_score >= float(self.thresholds.get("skim", 5.0)):
            return "快速浏览", "建议先看日报摘要，需要时再回到原文。"
        return "低优先级", "先保留记录，不建议本轮投入太多时间。"

    def _build_reason(
        self,
        item: ProcessedItem,
        breakdown: dict[str, float],
        total_score: float,
    ) -> str:
        """生成简洁的评分理由。"""

        sorted_dimensions = sorted(breakdown.items(), key=lambda pair: pair[1], reverse=True)
        labels = {
            "novelty": "新颖性",
            "execution_signal": "落地信号",
            "personal_relevance": "个人相关性",
        }
        reasons = [f"{labels[name]}较强（{score:.1f}）" for name, score in sorted_dimensions[:2]]

        if item.source == "github" and int(item.extra.get("stars", 0) or 0) > 0:
            reasons.append(f"GitHub Stars={int(item.extra.get('stars', 0) or 0)}")
        if item.source == "arxiv":
            reasons.append("适合持续做研究跟踪")

        return f"总分 {total_score:.1f}。{'；'.join(reasons[:3])}。"

    def _combined_text(self, item: ProcessedItem) -> str:
        """拼接评分所需文本。"""

        return " ".join(
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

    def _freshness_bonus(self, item: ProcessedItem) -> float:
        """根据发布时间给时效加分。"""

        if not item.published_at:
            return 0.0

        published = self._parse_datetime(item.published_at)
        if published is None:
            return 0.0

        delta_days = max((datetime.now(published.tzinfo) - published).days, 0)
        if delta_days <= 2:
            return 2.3
        if delta_days <= 7:
            return 1.8
        if delta_days <= 14:
            return 1.2
        if delta_days <= 30:
            return 0.6
        return 0.0

    def _parse_datetime(self, raw_value: str) -> datetime | None:
        """尽量兼容常见时间格式。"""

        try:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError:
            return None
