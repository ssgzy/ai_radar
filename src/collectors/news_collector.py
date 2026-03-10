"""AI 新闻站点采集器。"""

from __future__ import annotations

from src.collectors.feed_collector_base import BaseFeedCollector


class NewsCollector(BaseFeedCollector):
    """抓取 AI 新闻站点的 feed。"""

    source_name = "news"
