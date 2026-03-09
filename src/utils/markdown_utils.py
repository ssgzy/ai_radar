"""Markdown 文本拼装工具。"""

from __future__ import annotations


def bullet_items(items: list[str]) -> str:
    """把字符串列表拼装成 Markdown 列表。"""

    if not items:
        return "- 无"
    return "\n".join(f"- {item}" for item in items)


def quote_block(text: str) -> str:
    """把文本转换成 Markdown 引用块。"""

    if not text or text == "无":
        return "> 无"
    return "\n".join(f"> {line}" for line in text.splitlines())
