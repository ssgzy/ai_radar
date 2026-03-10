"""总结器解析逻辑测试。"""

from src.agents.summarizer import LocalOllamaSummarizer


def test_parse_sections_extracts_expected_fields(tmp_path):
    """验证固定标题文本可以被正确解析。"""

    summarizer = LocalOllamaSummarizer(
        host="http://localhost:11434",
        default_model="qwen3.5:9b",
        fallback_models=[],
        request_options={"timeout_seconds": 30},
        prompt_template="{content}",
        system_prompt="",
        debug_dir=tmp_path,
        console=None,  # type: ignore[arg-type]
    )

    response_text = """
【内容概述】
这是一个关于 AI Agent 的项目。

【解决的问题】
它试图降低多 Agent 协作的开发成本。

【为什么值得关注】
它提供了实用的工程落地路径。

【适合我关注的原因】
它适合做个人情报系统的后续扩展参考。

【关键词】
多 Agent、工程化、情报系统

【简洁引用】
让 Agent 协作更容易。
"""

    sections = summarizer._parse_sections(response_text)

    assert sections["内容概述"] == "这是一个关于 AI Agent 的项目。"
    assert sections["解决的问题"] == "它试图降低多 Agent 协作的开发成本。"
    assert sections["为什么值得关注"] == "它提供了实用的工程落地路径。"


def test_summarize_items_collects_failures(tmp_path):
    """验证单条总结失败时会记录 failed item，而不是中断整轮。"""

    summarizer = LocalOllamaSummarizer(
        host="http://localhost:11434",
        default_model="qwen3.5:9b",
        fallback_models=[],
        request_options={"timeout_seconds": 30},
        prompt_template="{content}",
        system_prompt="",
        debug_dir=tmp_path,
        console=None,  # type: ignore[arg-type]
    )

    class BoomClient:
        """返回固定异常的假客户端。"""

        def generate(self, prompt: str, item_label: str) -> tuple[str, str]:
            raise RuntimeError("mock generate failed")

    summarizer.client = BoomClient()  # type: ignore[assignment]

    from src.models import RawItem

    result = summarizer.summarize_items(
        items=[
            RawItem(
                source="rss",
                item_id="demo-1",
                title="Demo item",
                url="https://example.com/demo",
                published_at=None,
                content="demo content",
            )
        ],
        run_id="20260310_test",
    )

    assert result.processed_items == []
    assert len(result.failed_items) == 1
    assert result.failed_items[0].stage == "summarize"
    assert result.failed_items[0].source == "rss"
