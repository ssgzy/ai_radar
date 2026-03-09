"""Ollama 调用封装。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import os
import time
from typing import Any

import requests
from rich.console import Console


class OllamaClient:
    """负责与本地 Ollama 服务通信。"""

    def __init__(
        self,
        host: str,
        default_model: str,
        fallback_models: list[str],
        request_options: dict[str, Any],
        console: Console | None = None,
    ) -> None:
        self.host = host.rstrip("/")
        self.default_model = os.getenv("OLLAMA_MODEL", default_model)
        self.fallback_models = fallback_models
        self.request_options = request_options
        self.console = console

    def list_models(self) -> list[str]:
        """读取当前 Ollama 可用模型列表。"""

        response = requests.get(f"{self.host}/api/tags", timeout=20)
        response.raise_for_status()
        payload = response.json()
        return [model["name"] for model in payload.get("models", [])]

    def generate(self, prompt: str, item_label: str) -> tuple[str, str]:
        """尝试使用默认模型和回退模型生成文本。"""

        candidate_models = [self.default_model, *self.fallback_models]
        last_error: Exception | None = None

        for model_name in candidate_models:
            try:
                return self._generate_with_model(model_name=model_name, prompt=prompt, item_label=item_label)
            except Exception as error:  # noqa: BLE001
                last_error = error
                if self.console:
                    self.console.print(
                        f"[yellow]模型失败[/yellow] {model_name} | {item_label} | {error}"
                    )

        raise RuntimeError(f"Ollama 所有候选模型都失败了: {last_error}") from last_error

    def _generate_with_model(self, model_name: str, prompt: str, item_label: str) -> tuple[str, str]:
        """使用指定模型生成文本，并周期性输出等待心跳。"""

        timeout_seconds = int(self.request_options.get("timeout_seconds", 600))
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.request_options.get("temperature", 0.2),
                "top_p": self.request_options.get("top_p", 0.9),
            },
        }

        if self.console:
            self.console.print(
                f"[cyan]已发送模型请求[/cyan] {item_label} | 模型={model_name} | 等待模型返回"
            )
        started_at = time.monotonic()
        next_notice_at = 10

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                requests.post,
                f"{self.host}/api/generate",
                json=payload,
                timeout=(20, timeout_seconds),
            )

            while not future.done():
                elapsed = int(time.monotonic() - started_at)
                if self.console and elapsed >= next_notice_at:
                    self.console.print(
                        f"[blue]模型仍在生成[/blue] {item_label} | 模型={model_name} | 已等待 {elapsed} 秒"
                    )
                    next_notice_at += 10
                time.sleep(10)

            response = future.result()
            response.raise_for_status()
            response_text = response.json()["response"].strip()

        if self.console:
            self.console.print(
                f"[green]模型输出完成[/green] {item_label} | 模型={model_name} | 总计约 {len(response_text)} 字"
            )

        return response_text, model_name
