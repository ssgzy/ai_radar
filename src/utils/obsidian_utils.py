"""Obsidian 文件名与链接工具。"""

from __future__ import annotations

from src.utils.text_utils import safe_filename


def build_note_name(prefix: str, title: str) -> str:
    """生成稳定且可读的笔记文件名。"""

    return f"{prefix} - {safe_filename(title, limit=100)}"


def build_wikilink(note_name: str, alias: str | None = None) -> str:
    """生成 Wikilink 字符串。"""

    if alias:
        return f"[[{note_name}|{alias}]]"
    return f"[[{note_name}]]"
