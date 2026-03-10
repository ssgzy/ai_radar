"""管线级基础测试。"""

from pathlib import Path

from rich.console import Console

from src.pipeline import AIRadarPipeline


def test_pipeline_enabled_sources_filters_requested_sources(tmp_path):
    """验证手动指定来源时只返回被请求的启用来源。"""

    class DummySettings:
        """提供最小 settings 结构供测试使用。"""

        sources = {
            "sources": {
                "arxiv": {"enabled": True},
                "github": {"enabled": True},
            }
        }
        models = {"request": {}, "fallback_models": [], "default_model": "qwen3.5:9b"}
        prompts = {"summary_template": "{content}", "system_prompt": ""}
        scoring = {"scoring": {"dimensions": {}}, "tagging": {}}

        class paths:  # noqa: N801
            """最小路径占位。"""

            project_root = Path(tmp_path)
            raw_dir = Path(tmp_path / "raw")
            processed_dir = Path(tmp_path / "processed")
            logs_dir = Path(tmp_path / "logs")
            outputs_dir = Path(tmp_path / "outputs")
            obsidian_output_dir = Path(tmp_path / "obsidian")
            debug_dir = Path(tmp_path / "debug")
            state_dir = Path(tmp_path / "state")

    pipeline = AIRadarPipeline(  # type: ignore[arg-type]
        settings=DummySettings(),
        console=Console(),
        requested_sources=["github"],
    )

    assert pipeline._enabled_sources() == ["github"]
