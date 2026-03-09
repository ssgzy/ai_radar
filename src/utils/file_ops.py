"""文件读写相关工具。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> Path:
    """确保目录存在。"""

    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, content: str) -> Path:
    """写入 UTF-8 文本文件。"""

    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


def write_json(path: Path, data: Any) -> Path:
    """写入 JSON 文件。"""

    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_json(path: Path, default: Any) -> Any:
    """读取 JSON 文件；如果不存在则返回默认值。"""

    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))
