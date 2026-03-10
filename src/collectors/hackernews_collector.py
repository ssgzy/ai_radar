"""Hacker News 采集器。"""

from __future__ import annotations

import re
from typing import Any

import requests

from src.collectors.base_collector import BaseCollector
from src.models import RawItem
from src.utils.text_utils import normalize_whitespace, truncate_text


class HackerNewsCollector(BaseCollector):
    """通过官方 API 抓取与 AI 相关的 Hacker News 热门条目。"""

    source_name = "hackernews"

    def collect(self, max_items: int | None = None) -> list[RawItem]:
        """扫描热门条目并筛出 AI 相关内容。"""

        limit = max_items or int(self.source_config.get("max_items", 3))
        scan_limit = int(self.source_config.get("scan_limit", max(limit * 10, 30)))
        keywords = [keyword.lower() for keyword in self.source_config.get("keywords", [])]
        strong_keywords = [
            keyword.lower()
            for keyword in self.source_config.get("strong_keywords", keywords)
        ]
        weak_keywords = [
            keyword.lower()
            for keyword in self.source_config.get("weak_keywords", ["ai", "agent", "agents"])
        ]
        exclude_phrases = [
            phrase.lower()
            for phrase in self.source_config.get("exclude_phrases", [])
        ]
        min_relevance_score = float(self.source_config.get("min_relevance_score", 2.5))

        self.console.print(
            f"[bold cyan]开始采集 Hacker News[/bold cyan] | scan_limit={scan_limit} | max_items={limit}"
        )
        self.logger.info("Hacker News 采集开始 | scan_limit=%s | max_items=%s", scan_limit, limit)

        story_ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=20,
        ).json()

        items: list[RawItem] = []
        for index, story_id in enumerate(story_ids[:scan_limit], start=1):
            if len(items) >= limit:
                break

            story = self._fetch_story(story_id)
            if not story or story.get("type") != "story" or story.get("deleted") or story.get("dead"):
                continue

            title = normalize_whitespace(story.get("title"))
            url = normalize_whitespace(story.get("url")) or f"https://news.ycombinator.com/item?id={story_id}"
            combined_text = " ".join(
                [
                    title,
                    normalize_whitespace(story.get("text")),
                    url,
                ]
            ).lower()
            relevance_score, relevance_signals = self._score_relevance(
                title=title,
                body=normalize_whitespace(story.get("text")),
                url=url,
                strong_keywords=strong_keywords,
                weak_keywords=weak_keywords,
                exclude_phrases=exclude_phrases,
            )

            if keywords and not self._matches_keywords(combined_text, keywords):
                continue
            if relevance_score < min_relevance_score:
                continue

            self.console.print(
                f"[cyan]Hacker News[/cyan] {len(items) + 1}/{limit} | scan={index}/{scan_limit} | score={relevance_score:.1f} | {truncate_text(title, 90)}"
            )
            self.logger.info("Hacker News 条目 | index=%s | title=%s", index, title)

            items.append(
                RawItem(
                    source=self.source_name,
                    item_id=str(story_id),
                    title=title,
                    url=url,
                    published_at=self._story_time(story.get("time")),
                    authors=[normalize_whitespace(story.get("by"))] if story.get("by") else [],
                    content=self._build_content(story),
                    extra={
                        "hn_score": story.get("score", 0),
                        "hn_comments": story.get("descendants", 0),
                        "hn_item_url": f"https://news.ycombinator.com/item?id={story_id}",
                        "hn_relevance_score": relevance_score,
                        "hn_relevance_signals": relevance_signals,
                    },
                )
            )

        self.console.print(f"[green]完成 Hacker News 采集[/green] | 共 {len(items)} 条")
        self.logger.info("Hacker News 采集完成 | count=%s", len(items))
        return items

    def _fetch_story(self, story_id: int) -> dict[str, Any] | None:
        """读取单条 HN item。"""

        response = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def _build_content(self, story: dict[str, Any]) -> str:
        """为总结器拼装 HN 条目上下文。"""

        parts = [
            f"标题：{normalize_whitespace(story.get('title'))}",
            f"文本：{normalize_whitespace(story.get('text')) or '无正文'}",
            f"分数：{story.get('score', 0)}",
            f"评论数：{story.get('descendants', 0)}",
        ]
        return "\n".join(parts)

    def _story_time(self, unix_time: int | None) -> str | None:
        """把 UNIX 时间转换为 ISO 字符串。"""

        if unix_time is None:
            return None
        import datetime

        return datetime.datetime.fromtimestamp(unix_time, tz=datetime.timezone.utc).isoformat()

    def _matches_keywords(self, text: str, keywords: list[str]) -> bool:
        """用更严格的词边界规则做关键词匹配，避免误判。"""

        normalized_text = normalize_whitespace(text.lower())
        for keyword in keywords:
            normalized_keyword = normalize_whitespace(keyword.lower())
            if not normalized_keyword:
                continue

            if " " in normalized_keyword or len(normalized_keyword) > 3:
                if normalized_keyword in normalized_text:
                    return True
                continue

            pattern = rf"(?<![a-z0-9]){re.escape(normalized_keyword)}(?![a-z0-9])"
            if re.search(pattern, normalized_text):
                return True

        return False

    def _score_relevance(
        self,
        title: str,
        body: str,
        url: str,
        strong_keywords: list[str],
        weak_keywords: list[str],
        exclude_phrases: list[str],
    ) -> tuple[float, dict[str, list[str]]]:
        """根据标题、正文和 URL 计算条目与 AI 的相关性分数。"""

        normalized_title = normalize_whitespace(title.lower())
        normalized_body = normalize_whitespace(body.lower())
        normalized_url = normalize_whitespace(url.lower())
        title_and_url = f"{normalized_title} {normalized_url}".strip()

        if any(phrase and phrase in title_and_url for phrase in exclude_phrases):
            return 0.0, {"strong": [], "weak": [], "excluded": exclude_phrases}

        matched_title_strong = self._matched_keywords(normalized_title, strong_keywords)
        matched_url_strong = self._matched_keywords(normalized_url, strong_keywords)
        matched_body_strong = self._matched_keywords(normalized_body, strong_keywords)
        matched_title_weak = self._matched_keywords(normalized_title, weak_keywords)
        matched_url_weak = self._matched_keywords(normalized_url, weak_keywords)
        matched_body_weak = self._matched_keywords(normalized_body, weak_keywords)

        score = 0.0
        score += 3.0 * len(matched_title_strong)
        score += 2.0 * len(matched_url_strong)
        score += 1.5 * len(matched_body_strong)
        score += 2.0 * len(matched_title_weak)
        score += 1.0 * len(matched_url_weak)
        score += 0.5 * len(matched_body_weak)

        signals = {
            "strong": sorted(set(matched_title_strong + matched_url_strong + matched_body_strong)),
            "weak": sorted(set(matched_title_weak + matched_url_weak + matched_body_weak)),
            "excluded": [],
        }
        return score, signals

    def _matched_keywords(self, text: str, keywords: list[str]) -> list[str]:
        """返回某段文本实际命中的关键词列表。"""

        return [keyword for keyword in keywords if self._matches_keywords(text, [keyword])]
