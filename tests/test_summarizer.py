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
