"""采集器导出入口。"""

from src.collectors.arxiv_collector import ArxivCollector
from src.collectors.github_collector import GitHubCollector
from src.collectors.hackernews_collector import HackerNewsCollector
from src.collectors.news_collector import NewsCollector
from src.collectors.rss_collector import RSSCollector

__all__ = ["ArxivCollector", "GitHubCollector", "RSSCollector", "HackerNewsCollector", "NewsCollector"]
