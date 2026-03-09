"""JSON 序列化辅助函数。"""

from __future__ import annotations

import json
from typing import Any


def to_pretty_json(data: Any) -> str:
    """把 Python 对象转换成格式化 JSON 字符串。"""

    return json.dumps(data, ensure_ascii=False, indent=2)
