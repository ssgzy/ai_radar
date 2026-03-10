"""时间工具测试。"""

from src.utils.time_utils import timestamp_slug


def test_timestamp_slug_is_unique_across_fast_calls():
    """验证连续快速调用时，timestamp slug 仍然不同。"""

    first = timestamp_slug()
    second = timestamp_slug()

    assert first != second
