"""采集器导出入口。"""

from src.collectors.arxiv_collector import ArxivCollector
from src.collectors.github_collector import GitHubCollector

__all__ = ["ArxivCollector", "GitHubCollector"]
