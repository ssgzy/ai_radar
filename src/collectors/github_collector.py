"""GitHub 仓库采集器。"""

from __future__ import annotations

import os

import requests

from src.collectors.base_collector import BaseCollector
from src.models import RawItem
from src.utils.text_utils import normalize_whitespace, truncate_text


class GitHubCollector(BaseCollector):
    """抓取 GitHub 搜索结果。"""

    source_name = "github"

    def collect(self, max_items: int | None = None) -> list[RawItem]:
        """根据查询条件抓取 GitHub 仓库。"""

        query = self.source_config.get("query", "llm OR ai")
        limit = max_items or int(self.source_config.get("max_items", 3))
        headers = {"Accept": "application/vnd.github+json"}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        self.console.print(
            f"[bold cyan]开始采集 GitHub[/bold cyan] | query={query} | max_items={limit}"
        )
        self.logger.info("GitHub 采集开始 | query=%s | max_items=%s", query, limit)

        response = requests.get(
            "https://api.github.com/search/repositories",
            params={
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": limit,
            },
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        items: list[RawItem] = []
        for index, repo in enumerate(payload.get("items", []), start=1):
            title = normalize_whitespace(repo.get("full_name"))
            description = normalize_whitespace(repo.get("description")) or "仓库暂时没有填写描述。"
            language = repo.get("language") or "未知"
            stars = repo.get("stargazers_count", 0)
            self.console.print(
                f"[cyan]GitHub[/cyan] {index}/{limit} | {truncate_text(title, limit=90)}"
            )
            self.logger.info("GitHub 条目 | index=%s | title=%s", index, title)
            items.append(
                RawItem(
                    source=self.source_name,
                    item_id=str(repo.get("id")),
                    title=title,
                    url=repo.get("html_url", ""),
                    published_at=repo.get("updated_at"),
                    authors=[repo.get("owner", {}).get("login", "")],
                    content=(
                        f"仓库名称：{title}\n"
                        f"仓库描述：{description}\n"
                        f"主要语言：{language}\n"
                        f"Stars：{stars}"
                    ),
                    extra={
                        "description": description,
                        "language": language,
                        "stars": stars,
                        "forks": repo.get("forks_count"),
                        "open_issues": repo.get("open_issues_count"),
                    },
                )
            )

        self.console.print(f"[green]完成 GitHub 采集[/green] | 共 {len(items)} 条")
        self.logger.info("GitHub 采集完成 | count=%s", len(items))
        return items
