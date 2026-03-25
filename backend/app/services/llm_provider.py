from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import Settings


SCHEMA_HINTS = {
    "experience": (
        "输出 JSON 对象，字段必须仅包含：responsibilities, actions, results, metrics, tools_used, skills_inferred。"
        " 所有字段都使用数组；无信息时返回空数组。"
    ),
    "portrait": (
        "输出 JSON 对象，字段必须仅包含：student_type, capability_tags, behavior_tags, job_direction_tags,"
        " strengths, risks_or_gaps, portrait_summary, confidence_score。"
        " 标签字段用数组；portrait_summary 用字符串；confidence_score 用0到1之间数字。"
    ),
}


class ModelProvider:
    model_name = "unknown"

    def extract(self, prompt: str, schema_name: str) -> dict[str, Any]:
        raise NotImplementedError


class OpenAIModelProvider(ModelProvider):
    def __init__(self, settings: Settings) -> None:
        if not settings.llm_api_key.strip():
            raise ValueError("LLM_API_KEY is required when using real model provider.")
        self.model_name = settings.llm_model
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key
        self.timeout_seconds = settings.llm_timeout_seconds
        self.temperature = settings.llm_temperature

    def extract(self, prompt: str, schema_name: str) -> dict[str, Any]:
        schema_hint = SCHEMA_HINTS.get(schema_name, "输出一个严格 JSON 对象，不要包含额外文本。")
        body = {
            "model": self.model_name,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "system",
                    "content": "你是简历结构化抽取助手。必须输出严格 JSON，不要输出任何解释。",
                },
                {
                    "role": "user",
                    "content": f"{schema_hint}\n\n输入内容如下：\n{prompt}",
                },
            ],
            "response_format": {"type": "json_object"},
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )

        if response.status_code >= 400:
            raise RuntimeError(f"LLM request failed: {response.status_code} {response.text[:300]}")

        payload = response.json()
        message = payload.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "")
        if not isinstance(content, str):
            raise RuntimeError("LLM response content is not text.")

        parsed = self._parse_json_content(content)
        if not isinstance(parsed, dict):
            raise RuntimeError("LLM response is not a JSON object.")
        return parsed

    @staticmethod
    def _parse_json_content(content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 兼容模型偶发输出 markdown 代码块或夹杂说明文字
        fenced = re.search(r"```json\s*(\{.*\})\s*```", content, re.DOTALL)
        if fenced:
            return json.loads(fenced.group(1))

        object_match = re.search(r"(\{.*\})", content, re.DOTALL)
        if object_match:
            return json.loads(object_match.group(1))

        raise RuntimeError("Unable to parse JSON from LLM response.")


def build_provider(provider_name: str, settings: Settings) -> ModelProvider:
    normalized = provider_name.strip().lower()
    if normalized in {"openai", "real"}:
        return OpenAIModelProvider(settings)
    raise ValueError(f"Unsupported llm_provider: {provider_name}. Use 'openai'.")

