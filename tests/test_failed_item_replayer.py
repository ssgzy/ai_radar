"""失败条目回放测试。"""

from pathlib import Path

from rich.console import Console

from src.recovery import FailedItemReplayer


def test_failed_item_replayer_extracts_retriable_raw_items(tmp_path):
    """验证回放器能从 summarize 失败记录中提取 RawItem。"""

    class DummySettings:
        """提供最小 settings 结构供测试使用。"""

        models = {"request": {}, "fallback_models": [], "default_model": "qwen3.5:9b"}
        prompts = {"summary_template": "{content}", "system_prompt": ""}
        scoring = {"scoring": {"dimensions": {}}, "tagging": {}}

        class paths:  # noqa: N801
            """最小路径占位。"""

            raw_dir = Path(tmp_path / "raw")
            processed_dir = Path(tmp_path / "processed")
            debug_dir = Path(tmp_path / "debug")
            obsidian_output_dir = Path(tmp_path / "obsidian")
            outputs_dir = Path(tmp_path / "outputs")

    replayer = FailedItemReplayer(settings=DummySettings(), console=Console())  # type: ignore[arg-type]
    raw_items, skipped = replayer._collect_retriable_raw_items(
        payloads=[
            {
                "stage": "summarize",
                "extra": {
                    "raw_item": {
                        "source": "rss",
                        "item_id": "demo-1",
                        "title": "Demo title",
                        "url": "https://example.com/demo",
                        "published_at": None,
                        "authors": ["sam"],
                        "content": "demo content",
                        "extra": {"feed_name": "Demo Feed"},
                    }
                },
            },
            {"stage": "export_item_note", "extra": {}},
        ]
    )

    assert len(raw_items) == 1
    assert raw_items[0].title == "Demo title"
    assert skipped == 1
