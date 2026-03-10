"""Hacker News 关键词过滤测试。"""

from rich.console import Console

from src.collectors.hackernews_collector import HackerNewsCollector


def test_hackernews_keyword_matching_avoids_substring_false_positive():
    """验证关键词 `ai` 不会误命中普通单词内部子串。"""

    collector = HackerNewsCollector(
        source_config={"keywords": ["ai", "agent"]},
        console=Console(),
    )

    assert collector._matches_keywords("openai launches new agent stack", ["ai", "agent"]) is True
    assert collector._matches_keywords("repairers and activists gather globally", ["ai"]) is False


def test_hackernews_relevance_score_filters_weak_body_only_matches():
    """验证仅在正文里出现弱信号时不会被判为高相关。"""

    collector = HackerNewsCollector(
        source_config={},
        console=Console(),
    )

    score, signals = collector._score_relevance(
        title="Show HN: The Mog Programming Language",
        body="A simple language that can be used by AI agents.",
        url="https://example.com/mog",
        strong_keywords=["openai", "llm", "anthropic"],
        weak_keywords=["ai", "agent", "agents"],
        exclude_phrases=[],
    )

    assert score < 2.5
    assert signals["strong"] == []


def test_hackernews_relevance_score_accepts_strong_ai_signals():
    """验证带强 AI 信号的条目会通过相关性检查。"""

    collector = HackerNewsCollector(
        source_config={},
        console=Console(),
    )

    score, signals = collector._score_relevance(
        title="Anthropic launches code review tool for AI-generated code",
        body="The service helps teams review agentic coding workflows.",
        url="https://example.com/anthropic-code-review",
        strong_keywords=["anthropic", "llm", "agentic"],
        weak_keywords=["ai", "agent", "agents"],
        exclude_phrases=[],
    )

    assert score >= 2.5
    assert "anthropic" in signals["strong"]
