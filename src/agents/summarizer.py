"""本地 Ollama 中文总结器。"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from rich.console import Console

from src.models import ProcessedItem, RawItem
from src.utils.file_ops import write_text
from src.utils.ollama_client import OllamaClient
from src.utils.text_utils import normalize_whitespace, truncate_text


class LocalOllamaSummarizer:
    """使用本地 Ollama 对内容进行中文总结。"""

    SECTION_TITLES = [
        "内容概述",
        "解决的问题",
        "为什么值得关注",
        "适合我关注的原因",
        "关键词",
        "简洁引用",
    ]

    def __init__(
        self,
        host: str,
        default_model: str,
        fallback_models: list[str],
        request_options: dict[str, Any],
        prompt_template: str,
        system_prompt: str,
        debug_dir: Path,
        console: Console | None,
    ) -> None:
        self.console = console
        self.logger = logging.getLogger("summarizer")
        self.prompt_template = prompt_template
        self.system_prompt = system_prompt
        self.debug_prompt_dir = debug_dir / "prompts"
        self.debug_response_dir = debug_dir / "responses"
        self.client = OllamaClient(
            host=host,
            default_model=default_model,
            fallback_models=fallback_models,
            request_options=request_options,
            console=console,
        )

    def summarize_items(self, items: list[RawItem], run_id: str) -> list[ProcessedItem]:
        """批量总结多个原始条目。"""

        processed_items: list[ProcessedItem] = []
        total = len(items)

        for index, item in enumerate(items, start=1):
            label = f"{item.source} {index}/{total} | {truncate_text(item.title, limit=70)}"
            if self.console:
                self.console.print(f"[magenta]开始总结[/magenta] {label}")
            self.logger.info("开始总结 | label=%s", label)

            prompt = self._build_prompt(item=item)
            prompt_path = self._save_debug_prompt(run_id=run_id, item=item, prompt=prompt)

            response_text, model_name = self.client.generate(prompt=prompt, item_label=label)
            response_path = self._save_debug_response(
                run_id=run_id,
                item=item,
                response_text=response_text,
            )
            sections = self._parse_sections(response_text)

            processed_items.append(
                ProcessedItem(
                    source=item.source,
                    item_id=item.item_id,
                    title=item.title,
                    url=item.url,
                    published_at=item.published_at,
                    authors=item.authors,
                    raw_content=item.content,
                    content_overview_cn=sections.get("内容概述", ""),
                    problem_cn=sections.get("解决的问题", ""),
                    why_it_matters_cn=sections.get("为什么值得关注", ""),
                    why_follow_cn=sections.get("适合我关注的原因", ""),
                    keywords=self._split_keywords(sections.get("关键词", "")),
                    quote_cn=sections.get("简洁引用", "无"),
                    model_name=model_name,
                    prompt_path=str(prompt_path),
                    response_path=str(response_path),
                    extra=item.extra,
                )
            )

            if self.console:
                self.console.print(f"[green]总结完成[/green] {label} | 模型={model_name}")
            self.logger.info("总结完成 | label=%s | model=%s", label, model_name)

        return processed_items

    def _build_prompt(self, item: RawItem) -> str:
        """组装单条内容的总结提示词。"""

        content = normalize_whitespace(item.content)
        return (
            f"{self.system_prompt.strip()}\n\n"
            + self.prompt_template.format(
                source_name=item.source,
                title=item.title,
                url=item.url,
                published_at=item.published_at or "未知",
                content=content,
            )
        )

    def _save_debug_prompt(self, run_id: str, item: RawItem, prompt: str) -> Path:
        """保存发给模型的 prompt。"""

        filename = f"{run_id}_{item.source}_{item.item_id}_prompt.txt"
        return write_text(self.debug_prompt_dir / filename, prompt)

    def _save_debug_response(self, run_id: str, item: RawItem, response_text: str) -> Path:
        """保存模型原始返回。"""

        filename = f"{run_id}_{item.source}_{item.item_id}_response.txt"
        return write_text(self.debug_response_dir / filename, response_text)

    def _parse_sections(self, response_text: str) -> dict[str, str]:
        """从固定标题文本中提取结构化字段。"""

        sections: dict[str, str] = {}
        matches = list(re.finditer(r"【([^】]+)】", response_text))
        for index, match in enumerate(matches):
            title = match.group(1).strip()
            if title not in self.SECTION_TITLES:
                continue
            content_start = match.end()
            content_end = matches[index + 1].start() if index + 1 < len(matches) else len(response_text)
            sections[title] = self._clean_section_text(response_text[content_start:content_end])

        if "内容概述" not in sections:
            # 模型偶尔会偏离格式，这里保底保留完整输出，避免丢失结果。
            sections["内容概述"] = self._clean_section_text(response_text)
            sections.setdefault("解决的问题", "")
            sections.setdefault("为什么值得关注", "")
            sections.setdefault("适合我关注的原因", "")
            sections.setdefault("关键词", "")
            sections.setdefault("简洁引用", "无")

        return sections

    def _split_keywords(self, raw_keywords: str) -> list[str]:
        """把顿号或逗号分隔的关键词转成列表。"""

        normalized = raw_keywords.replace("，", "、").replace(",", "、")
        return [self._clean_section_text(keyword) for keyword in normalized.split("、") if keyword.strip()]

    def _clean_section_text(self, text: str) -> str:
        """去掉模型常见的 Markdown 噪音。"""

        cleaned = normalize_whitespace(text)
        cleaned = cleaned.replace("**", "").replace("__", "").strip()
        cleaned = re.sub(r"^[\-•\s]+", "", cleaned)
        cleaned = re.sub(r"\s+([。，“”！？])", r"\1", cleaned)
        return cleaned.strip()
