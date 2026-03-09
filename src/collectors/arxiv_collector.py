"""arXiv 采集器。"""

from __future__ import annotations

import arxiv

from src.collectors.base_collector import BaseCollector
from src.models import RawItem
from src.utils.text_utils import normalize_whitespace, truncate_text


class ArxivCollector(BaseCollector):
    """抓取 arXiv 最新论文。"""

    source_name = "arxiv"

    def collect(self, max_items: int | None = None) -> list[RawItem]:
        """根据查询条件抓取 arXiv 内容。"""

        query = self.source_config.get("query", "cat:cs.AI")
        limit = max_items or int(self.source_config.get("max_items", 3))

        self.console.print(
            f"[bold cyan]开始采集 arXiv[/bold cyan] | query={query} | max_items={limit}"
        )
        self.logger.info("arXiv 采集开始 | query=%s | max_items=%s", query, limit)

        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

        items: list[RawItem] = []
        for index, result in enumerate(client.results(search), start=1):
            title = normalize_whitespace(result.title)
            self.console.print(
                f"[cyan]arXiv[/cyan] {index}/{limit} | {truncate_text(title, limit=90)}"
            )
            self.logger.info("arXiv 条目 | index=%s | title=%s", index, title)
            items.append(
                RawItem(
                    source=self.source_name,
                    item_id=result.get_short_id(),
                    title=title,
                    url=result.entry_id,
                    published_at=result.published.isoformat() if result.published else None,
                    authors=[author.name for author in result.authors],
                    content=normalize_whitespace(result.summary),
                    extra={
                        "pdf_url": result.pdf_url,
                        "comment": normalize_whitespace(result.comment),
                        "primary_category": result.primary_category,
                    },
                )
            )

        self.console.print(f"[green]完成 arXiv 采集[/green] | 共 {len(items)} 条")
        self.logger.info("arXiv 采集完成 | count=%s", len(items))
        return items
