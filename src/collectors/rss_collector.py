"""通用 RSS 采集器。"""

from __future__ import annotations

from src.collectors.feed_collector_base import BaseFeedCollector


class RSSCollector(BaseFeedCollector):
    """抓取常规 RSS/Blog feed。"""

    source_name = "rss"
