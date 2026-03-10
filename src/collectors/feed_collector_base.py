"""基于 RSS/Atom 的通用 feed 采集器基类。"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from math import ceil
from typing import Any

import feedparser
import requests

from src.collectors.base_collector import BaseCollector
from src.models import RawItem
from src.utils.text_utils import normalize_whitespace, truncate_text


class BaseFeedCollector(BaseCollector):
    """封装 RSS/Atom feed 的通用抓取逻辑。"""

    source_name = "feed"

    def collect(self, max_items: int | None = None) -> list[RawItem]:
        """从多个 feed 中抓取并合并内容。"""

        feeds = self.source_config.get("feeds", [])
        limit = max_items or int(self.source_config.get("max_items", 3))
        if not feeds:
            self.console.print(f"[yellow]{self.source_name} 未配置 feeds[/yellow]")
            return []

        per_feed_limit = max(1, ceil(limit / max(len(feeds), 1)))
        self.console.print(
            f"[bold cyan]开始采集 {self.source_name}[/bold cyan] | feeds={len(feeds)} | max_items={limit}"
        )
        self.logger.info("%s 采集开始 | feeds=%s | max_items=%s", self.source_name, len(feeds), limit)

        items: list[RawItem] = []
        for feed_index, feed_config in enumerate(feeds, start=1):
            feed_name = feed_config.get("name", "Unknown Feed")
            feed_url = feed_config.get("url", "")
            self.console.print(
                f"[cyan]{self.source_name}[/cyan] feed {feed_index}/{len(feeds)} | {feed_name}"
            )
            self.logger.info("%s feed 开始 | name=%s | url=%s", self.source_name, feed_name, feed_url)

            items.extend(
                self._collect_from_feed(
                    feed_name=feed_name,
                    feed_url=feed_url,
                    max_items=per_feed_limit,
                )
            )

        sorted_items = sorted(items, key=lambda item: item.published_at or "", reverse=True)
        final_items = sorted_items[:limit]
        self.console.print(f"[green]完成 {self.source_name} 采集[/green] | 共 {len(final_items)} 条")
        self.logger.info("%s 采集完成 | count=%s", self.source_name, len(final_items))
        return final_items

    def _collect_from_feed(self, feed_name: str, feed_url: str, max_items: int) -> list[RawItem]:
        """抓取单个 feed 的条目。"""

        response = requests.get(feed_url, timeout=30, headers={"User-Agent": "AI-Radar/0.1"})
        response.raise_for_status()
        parsed_feed = feedparser.parse(response.content)

        items: list[RawItem] = []
        for index, entry in enumerate(parsed_feed.entries[:max_items], start=1):
            title = normalize_whitespace(entry.get("title"))
            link = normalize_whitespace(entry.get("link"))
            summary = self._build_entry_content(entry)
            published_at = self._entry_published_at(entry)
            original_entry_id = normalize_whitespace(
                str(entry.get("id") or link or title or f"{feed_name}-{index}")
            )
            item_id = hashlib.sha1(original_entry_id.encode("utf-8")).hexdigest()[:16]

            self.console.print(
                f"[cyan]{self.source_name}[/cyan] {feed_name} {index}/{max_items} | {truncate_text(title, 90)}"
            )
            self.logger.info(
                "%s 条目 | feed=%s | index=%s | title=%s",
                self.source_name,
                feed_name,
                index,
                title,
            )

            items.append(
                RawItem(
                    source=self.source_name,
                    item_id=item_id,
                    title=title,
                    url=link,
                    published_at=published_at,
                    authors=[normalize_whitespace(entry.get("author"))] if entry.get("author") else [],
                    content=summary,
                    extra={
                        "entry_id": original_entry_id,
                        "feed_name": feed_name,
                        "feed_url": feed_url,
                        "source_feed_title": normalize_whitespace(parsed_feed.feed.get("title", feed_name)),
                    },
                )
            )

        return items

    def _build_entry_content(self, entry: Any) -> str:
        """拼装 feed 条目的正文摘要。"""

        parts: list[str] = []
        summary = normalize_whitespace(entry.get("summary") or entry.get("description"))
        if summary:
            parts.append(summary)

        content_blocks = entry.get("content", [])
        if content_blocks:
            first_block = content_blocks[0]
            value = normalize_whitespace(first_block.get("value")) if isinstance(first_block, dict) else ""
            if value and value not in parts:
                parts.append(value)

        return "\n".join(parts).strip()

    def _entry_published_at(self, entry: Any) -> str | None:
        """把 feedparser 时间结构转换成 ISO 时间。"""

        published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if not published_struct:
            return None

        published_dt = datetime(*published_struct[:6], tzinfo=timezone.utc)
        return published_dt.isoformat()
