"""Agent 模块导出入口。"""

from src.agents.deduper import DeduplicationResult, HeuristicDeduper
from src.agents.quality_gate import QualityDecision, QualityGateResult, SourceQualityGate
from src.agents.scorer import HeuristicScorer
from src.agents.summarizer import LocalOllamaSummarizer, SummarizationResult
from src.agents.tagger import KeywordTagger
from src.agents.topic_aggregator import TopicAggregator

__all__ = [
    "LocalOllamaSummarizer",
    "SummarizationResult",
    "HeuristicScorer",
    "KeywordTagger",
    "HeuristicDeduper",
    "DeduplicationResult",
    "SourceQualityGate",
    "QualityGateResult",
    "QualityDecision",
    "TopicAggregator",
]
