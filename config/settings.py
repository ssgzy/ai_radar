"""集中加载项目配置和路径。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(slots=True)
class AppPaths:
    """保存项目常用目录路径。"""

    project_root: Path
    config_dir: Path
    data_dir: Path
    raw_dir: Path
    processed_dir: Path
    state_dir: Path
    logs_dir: Path
    outputs_dir: Path
    debug_dir: Path
    obsidian_docs_dir: Path
    obsidian_output_dir: Path


@dataclass(slots=True)
class AppSettings:
    """保存运行所需配置内容。"""

    paths: AppPaths
    sources: dict[str, Any]
    models: dict[str, Any]
    prompts: dict[str, Any]
    scoring: dict[str, Any]
    obsidian: dict[str, Any]


def _read_yaml(path: Path) -> dict[str, Any]:
    """读取 YAML 配置文件。"""

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_settings(project_root: Path | None = None) -> AppSettings:
    """加载当前项目的全部配置。"""

    base_dir = project_root or Path(__file__).resolve().parent.parent
    load_dotenv(base_dir / ".env")

    paths = AppPaths(
        project_root=base_dir,
        config_dir=base_dir / "config",
        data_dir=base_dir / "data",
        raw_dir=base_dir / "data" / "raw",
        processed_dir=base_dir / "data" / "processed",
        state_dir=base_dir / "data" / "state",
        logs_dir=base_dir / "logs",
        outputs_dir=base_dir / "outputs",
        debug_dir=base_dir / "outputs" / "debug",
        obsidian_docs_dir=base_dir / "obsidian",
        obsidian_output_dir=base_dir / "outputs" / "obsidian",
    )

    return AppSettings(
        paths=paths,
        sources=_read_yaml(paths.config_dir / "sources.yaml"),
        models=_read_yaml(paths.config_dir / "models.yaml"),
        prompts=_read_yaml(paths.config_dir / "prompts.yaml"),
        scoring=_read_yaml(paths.config_dir / "scoring.yaml"),
        obsidian=_read_yaml(paths.config_dir / "obsidian.yaml"),
    )
