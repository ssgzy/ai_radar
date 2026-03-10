"""质量过滤器测试。"""

from src.agents.quality_gate import SourceQualityGate
from src.models import ProcessedItem


def test_quality_gate_filters_low_signal_news_item():
    """低分且缺少主题信号的资讯应该被过滤。"""

    gate = SourceQualityGate(
        {
            "keep_all_sources": ["arxiv", "github"],
            "source_min_scores": {"news": 5.0},
            "preferred_topic_tags": ["Agent", "大模型", "开发工具"],
            "focus_keywords": {"strong": ["agent", "llm"], "medium": ["developer"]},
            "minimum_focus_signals": {"news": 1},
            "blocked_title_keywords": ["giveaway"],
            "blocked_body_keywords": ["register now"],
        }
    )

    item = ProcessedItem(
        source="news",
        item_id="n1",
        title="Conference recap for general cloud teams",
        url="https://example.com/news",
        published_at=None,
        raw_content="A broad market recap for general cloud teams.",
        total_score=4.2,
        tags=["新闻站点"],
    )

    result = gate.filter_items([item])

    assert len(result.kept_items) == 0
    assert len(result.filtered_items) == 1
    assert result.decisions[0].keep is False
    assert item.quality_decision == "filter"


def test_quality_gate_keeps_core_sources_by_default():
    """核心来源即使分数较低也应该默认保留。"""

    gate = SourceQualityGate({"keep_all_sources": ["arxiv", "github"]})
    item = ProcessedItem(
        source="github",
        item_id="g1",
        title="tiny ai repo",
        url="https://example.com/repo",
        published_at=None,
        raw_content="small repo",
        total_score=2.5,
        tags=["GitHub 项目"],
    )

    result = gate.filter_items([item])

    assert len(result.kept_items) == 1
    assert result.decisions[0].keep is True
    assert item.quality_decision == "keep"
