"""基于标签和关键词的主题聚合器。"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Any

from src.models import ProcessedItem, TopicCluster


class TopicAggregator:
    """把去重后的条目聚合成便于阅读的主题块。"""

    def __init__(self, dashboard_config: dict[str, Any]) -> None:
        self.logger = logging.getLogger("topic")
        self.dashboard_config = dashboard_config or {}
        self.topic_priority = self.dashboard_config.get(
            "topic_priority",
            ["Agent", "开发工具", "自动化", "本地 AI", "多模态", "评测与基准", "大模型"],
        )
        self.max_topics = int(self.dashboard_config.get("max_topics", 5))
        self.max_items_per_topic = int(self.dashboard_config.get("max_items_per_topic", 4))
        self.ignored_tags = {
            "论文",
            "GitHub 项目",
            "RSS 订阅",
            "新闻站点",
            "Hacker News",
            "研究跟踪",
            "高星信号",
            "待分类",
        }

    def build_clusters(self, items: list[ProcessedItem]) -> list[TopicCluster]:
        """为一批条目生成主题聚合。"""

        grouped: dict[str, list[ProcessedItem]] = defaultdict(list)
        for item in items:
            topic_name = self._primary_topic(item)
            item.topic_name = topic_name
            grouped[topic_name].append(item)

        clusters: list[TopicCluster] = []
        for topic_name, topic_items in grouped.items():
            ordered_items = sorted(topic_items, key=lambda entry: entry.total_score, reverse=True)
            keyword_counter: Counter[str] = Counter()
            source_counter: Counter[str] = Counter(entry.source for entry in ordered_items)
            for item in ordered_items:
                keyword_counter.update(keyword for keyword in item.keywords if keyword)
                keyword_counter.update(
                    tag for tag in item.tags if tag and tag not in self.ignored_tags and tag != topic_name
                )

            top_keywords = [keyword for keyword, _ in keyword_counter.most_common(5)]
            avg_score = round(sum(item.total_score for item in ordered_items) / max(len(ordered_items), 1), 1)
            max_score = round(max(item.total_score for item in ordered_items), 1)
            summary_cn = self._build_summary(
                topic_name=topic_name,
                item_count=len(ordered_items),
                source_counter=source_counter,
                top_keywords=top_keywords,
            )
            cluster_items = [
                {
                    "title": item.title,
                    "source": item.source,
                    "total_score": item.total_score,
                    "priority_level": item.priority_level,
                    "note_path": item.note_path,
                    "topic_name": topic_name,
                }
                for item in ordered_items[: self.max_items_per_topic]
            ]
            clusters.append(
                TopicCluster(
                    topic_name=topic_name,
                    item_count=len(ordered_items),
                    avg_score=avg_score,
                    max_score=max_score,
                    source_counts=dict(source_counter),
                    top_keywords=top_keywords,
                    summary_cn=summary_cn,
                    items=cluster_items,
                )
            )
            self.logger.info(
                "主题聚合 | topic=%s | items=%s | avg_score=%.1f",
                topic_name,
                len(ordered_items),
                avg_score,
            )

        return sorted(
            clusters,
            key=lambda cluster: (cluster.avg_score, cluster.item_count, cluster.max_score),
            reverse=True,
        )[: self.max_topics]

    def _primary_topic(self, item: ProcessedItem) -> str:
        """根据标签优先级为条目选择主主题。"""

        for tag_name in self.topic_priority:
            if tag_name in item.tags:
                return tag_name

        remaining_tags = [tag for tag in item.tags if tag not in self.ignored_tags]
        if remaining_tags:
            return remaining_tags[0]
        if item.source == "arxiv":
            return "研究跟踪"
        if item.source == "github":
            return "项目动态"
        return "其他情报"

    def _build_summary(
        self,
        topic_name: str,
        item_count: int,
        source_counter: Counter[str],
        top_keywords: list[str],
    ) -> str:
        """构造简洁的主题摘要。"""

        source_text = "、".join(
            f"{source} {count} 条" for source, count in source_counter.most_common(3)
        ) or "暂无来源"
        keyword_text = "、".join(top_keywords[:4]) or "暂无稳定关键词"
        return f"本轮围绕「{topic_name}」共聚合 {item_count} 条内容，来源以 {source_text} 为主，重点关键词包括 {keyword_text}。"
