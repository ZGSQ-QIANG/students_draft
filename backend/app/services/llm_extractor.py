from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.services.llm_provider import build_provider


class LLMExtractor:
    def __init__(self) -> None:
        settings = get_settings()
        self.provider = build_provider(settings.llm_provider, settings)

    def enrich_experiences(self, kind: str, sections: list[str], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for index, section in enumerate(sections):
            rule_payload = rules[index] if index < len(rules) else {}
            prompt = self._build_experience_prompt(kind, section, rule_payload)
            llm_payload = self.provider.extract(prompt, "experience")
            enriched.append({**rule_payload, **llm_payload})
        return enriched

    def generate_portrait(self, normalized_payload: dict[str, Any], sections: dict[str, list[str]]) -> dict[str, Any]:
        prompt = self._build_portrait_prompt(normalized_payload, sections)
        return self.provider.extract(prompt, "portrait")

    @staticmethod
    def _build_experience_prompt(kind: str, section: str, rule_payload: dict[str, Any]) -> str:
        return "\n".join(
            [
                f"类型: {kind}",
                "原文:",
                section,
                "规则结果:",
                json.dumps(rule_payload, ensure_ascii=False),
            ]
        )

    @staticmethod
    def _build_portrait_prompt(normalized_payload: dict[str, Any], sections: dict[str, list[str]]) -> str:
        return "\n".join(
            [
                "请基于以下学生简历信息生成画像候选。",
                json.dumps(normalized_payload, ensure_ascii=False),
                "原始模块:",
                json.dumps(sections, ensure_ascii=False),
            ]
        )
