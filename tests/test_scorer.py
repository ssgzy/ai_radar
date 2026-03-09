"""评分器测试。"""

from src.agents.scorer import HeuristicScorer
from src.models import ProcessedItem


def test_heuristic_scorer_populates_scores_and_priority():
    """验证评分器会写入分数和推荐级别。"""

    scorer = HeuristicScorer(
        {
            "dimensions": {
                "novelty": {"weight": 0.35},
                "execution_signal": {"weight": 0.3},
                "personal_relevance": {"weight": 0.35},
            },
            "thresholds": {"high_priority": 8.0, "watchlist": 6.5, "skim": 5.0},
            "interest_keywords": {"strong": ["agent", "local-first"], "medium": ["developer"]},
            "novelty_keywords": ["agent", "benchmark"],
            "execution_keywords": ["open-source", "workflow"],
        }
    )

    item = ProcessedItem(
        source="github",
        item_id="1",
        title="Local-first agent workspace",
        url="https://example.com",
        published_at="2026-03-10T00:00:00+00:00",
        raw_content="Open-source workflow for agent developers.",
        tags=["GitHub 项目", "Agent", "本地 AI"],
        extra={"stars": 25, "language": "Python", "description": "demo"},
    )

    scored_item = scorer.score_items([item])[0]

    assert scored_item.total_score > 0
    assert scored_item.priority_level in {"高优先级跟进", "重点关注", "快速浏览", "低优先级"}
    assert set(scored_item.score_breakdown) == {"novelty", "execution_signal", "personal_relevance"}
