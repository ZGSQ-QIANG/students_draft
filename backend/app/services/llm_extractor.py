from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.services.dictionaries import (
    ACADEMIC_POTENTIAL_TAGS,
    BEHAVIOR_TAGS,
    CAPABILITY_TAGS,
    JOB_DIRECTION_TAGS,
    METHOD_TAGS,
    RESEARCH_DIRECTION_TAGS,
    STUDENT_TYPES,
)
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

    def generate_portrait(self, normalized_payload: dict[str, Any], sections: dict[str, list[str]], mode: str = "student") -> dict[str, Any]:
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
        lines = [
            "请基于以下学生简历信息生成画像候选。",
            json.dumps(normalized_payload, ensure_ascii=False),
            "原始模块:",
            json.dumps(sections, ensure_ascii=False),
            "硬性约束：标签必须从给定词典中选择，禁止自造词。",
            f"student_type 可选：{STUDENT_TYPES}",
            f"research_direction_tags 可选：{RESEARCH_DIRECTION_TAGS}",
            f"method_tags 可选：{METHOD_TAGS}",
            f"academic_potential_tags 可选：{ACADEMIC_POTENTIAL_TAGS}",
            f"capability_tags 可选：{CAPABILITY_TAGS}",
            f"behavior_tags 可选：{BEHAVIOR_TAGS}",
            f"job_direction_tags 可选：{JOB_DIRECTION_TAGS}",
        ]
        lines.append("仅输出 JSON 对象，不要输出解释。")
        return "\n".join(lines)
