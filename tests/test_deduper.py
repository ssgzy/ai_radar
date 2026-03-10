"""去重器测试。"""

from src.agents.deduper import HeuristicDeduper
from src.models import ProcessedItem


def test_heuristic_deduper_removes_duplicate_titles():
    """验证相同标题的条目会被去重。"""

    deduper = HeuristicDeduper()
    item_a = ProcessedItem(
        source="rss",
        item_id="1",
        title="OpenAI launches new local AI workflow",
        url="https://example.com/a",
        published_at=None,
        total_score=6.5,
    )
    item_b = ProcessedItem(
        source="news",
        item_id="2",
        title="OpenAI launches new local AI workflow",
        url="https://another.example.com/post",
        published_at=None,
        total_score=5.9,
    )

    result = deduper.dedupe_items([item_b, item_a])

    assert len(result.unique_items) == 1
    assert len(result.duplicates) == 1
    assert result.unique_items[0].title == "OpenAI launches new local AI workflow"
