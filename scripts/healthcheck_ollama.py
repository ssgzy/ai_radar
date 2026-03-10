"""检查本地 Ollama 服务和模型可用性。"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    # 让脚本从 scripts/ 目录直接执行时也能导入项目包。
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import load_settings
from src.utils.logger import get_console
from src.utils.ollama_client import OllamaClient


def main() -> None:
    """打印模型列表并做一次最小生成测试。"""

    settings = load_settings()
    console = get_console()
    client = OllamaClient(
        host="http://localhost:11434",
        default_model=settings.models.get("default_model", "qwen3.5:9b"),
        fallback_models=settings.models.get("fallback_models", []),
        request_options=settings.models.get("request", {}),
        console=console,
    )

    console.print("[bold cyan]检查 Ollama 模型列表[/bold cyan]")
    models = client.list_models()
    for model_name in models:
        console.print(f"- {model_name}")

    console.print("[bold cyan]执行最小生成测试[/bold cyan]")
    result, used_model = client.generate(
        prompt="请用中文一句话说明 AI Radar 是什么。",
        item_label="ollama healthcheck",
    )
    console.print(f"[green]成功[/green] | 模型={used_model} | 输出={result}")


if __name__ == "__main__":
    main()
