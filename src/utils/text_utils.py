"""文本清洗和文件名处理工具。"""

from __future__ import annotations

import re


def normalize_whitespace(text: str | None) -> str:
    """把连续空白折叠成单个空格。"""

    return re.sub(r"\s+", " ", (text or "")).strip()


def truncate_text(text: str, limit: int = 120) -> str:
    """在日志中安全地截断长文本。"""

    clean_text = normalize_whitespace(text)
    if len(clean_text) <= limit:
        return clean_text
    return f"{clean_text[: limit - 3]}..."


def safe_filename(text: str, limit: int = 120) -> str:
    """把任意标题转换成相对稳健的文件名。"""

    cleaned = re.sub(r"[\\/:*?\"<>|#\[\]]+", " ", text)
    cleaned = normalize_whitespace(cleaned).strip(". ")
    cleaned = cleaned[:limit].rstrip()
    return cleaned or "untitled"
