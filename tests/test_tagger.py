"""标签器测试。"""

from src.agents.tagger import KeywordTagger
from src.models import ProcessedItem


def test_keyword_tagger_assigns_expected_tags():
    """验证关键词命中时会生成合理标签。"""

    tagger = KeywordTagger(
        {
            "topics": {
                "Agent": ["agent"],
                "本地 AI": ["local-first"],
            },
            "source_tags": {"github": "GitHub 项目"},
        }
    )

    item = ProcessedItem(
        source="github",
        item_id="1",
        title="Local-first agent workspace",
        url="https://example.com",
        published_at=None,
        raw_content="An open-source local-first agent toolkit.",
    )

    tagged_item = tagger.tag_items([item])[0]

    assert "GitHub 项目" in tagged_item.tags
    assert "Agent" in tagged_item.tags
    assert "本地 AI" in tagged_item.tags
