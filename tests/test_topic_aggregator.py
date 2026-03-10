"""主题聚合器测试。"""

from src.agents.topic_aggregator import TopicAggregator
from src.models import ProcessedItem


def test_topic_aggregator_groups_items_by_priority_tags():
    """带优先主题标签的条目应该聚合到稳定主题。"""

    aggregator = TopicAggregator(
        {
            "topic_priority": ["Agent", "开发工具", "自动化", "大模型"],
            "max_topics": 5,
            "max_items_per_topic": 3,
        }
    )

    items = [
        ProcessedItem(
            source="github",
            item_id="1",
            title="Agent workspace",
            url="https://example.com/1",
            published_at=None,
            tags=["GitHub 项目", "Agent", "开发工具"],
            keywords=["agent", "workspace"],
            total_score=8.4,
            note_path="/tmp/agent-workspace.md",
        ),
        ProcessedItem(
            source="news",
            item_id="2",
            title="Anthropic code review tool",
            url="https://example.com/2",
            published_at=None,
            tags=["新闻站点", "开发工具", "大模型"],
            keywords=["code review", "anthropic"],
            total_score=6.0,
            note_path="/tmp/code-review.md",
        ),
    ]

    clusters = aggregator.build_clusters(items)

    assert len(clusters) == 2
    assert clusters[0].topic_name == "Agent"
    assert items[0].topic_name == "Agent"
    assert items[1].topic_name == "开发工具"
