from __future__ import annotations

import re
from typing import Any

from app.services.dictionaries import (
    ACADEMIC_POTENTIAL_TAGS,
    BEHAVIOR_TAGS,
    CAPABILITY_TAGS,
    DEGREES,
    JOB_DIRECTION_TAGS,
    METHOD_TAGS,
    RESEARCH_DIRECTION_TAGS,
    SCHOOL_LEVEL_MAP,
    SCHOOL_LEVELS,
)


class Normalizer:
    def normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        basic = payload.get("basic_info") or {}
        if basic.get("highest_degree") not in DEGREES:
            basic["highest_degree"] = self._normalize_degree(basic.get("highest_degree"))
        for education in payload.get("educations", []):
            education["degree"] = self._normalize_degree(education.get("degree"))
            education["gpa_normalized"] = self._normalize_gpa(education.get("gpa_raw"))
            education["school_level"] = self._normalize_school_level(
                education.get("school_name"),
                education.get("school_level"),
            )
        portrait = payload.get("portrait") or {}
        portrait["capability_tags"] = self._filter_tags(portrait.get("capability_tags", []), CAPABILITY_TAGS)
        portrait["behavior_tags"] = self._filter_tags(portrait.get("behavior_tags", []), BEHAVIOR_TAGS)
        portrait["job_direction_tags"] = self._filter_tags(portrait.get("job_direction_tags", []), JOB_DIRECTION_TAGS)
        portrait["research_direction_tags"] = self._filter_tags(portrait.get("research_direction_tags", []), RESEARCH_DIRECTION_TAGS)
        portrait["method_tags"] = self._filter_tags(portrait.get("method_tags", []), METHOD_TAGS)
        portrait["academic_potential_tags"] = self._filter_tags(
            portrait.get("academic_potential_tags", []), ACADEMIC_POTENTIAL_TAGS
        )
        payload["basic_info"] = basic
        payload["portrait"] = portrait
        return payload

    @staticmethod
    def _normalize_degree(value: str | None) -> str | None:
        if not value:
            return None
        for degree in DEGREES:
            if degree in value:
                return degree
        return value

    @staticmethod
    def _normalize_gpa(value: str | None) -> float | None:
        if not value:
            return None
        nums = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", value)]
        if not nums:
            return None
        if len(nums) >= 2 and nums[1] in (4.0, 5.0, 100.0):
            return round(nums[0] / nums[1] * 4, 2) if nums[1] != 4.0 else round(nums[0], 2)
        if nums[0] > 4:
            return round(nums[0] / 100 * 4, 2)
        return round(nums[0], 2)

    @staticmethod
    def _normalize_school_level(school_name: str | None, current_level: str | None = None) -> str:
        if current_level:
            for level in SCHOOL_LEVELS:
                if level != "未知" and level in current_level:
                    return level
        if not school_name:
            return "未知"
        normalized_name = re.sub(r"\s+", "", school_name)
        for known_name, level in SCHOOL_LEVEL_MAP.items():
            if known_name in normalized_name or normalized_name in known_name:
                return level
        if "职业" in normalized_name or "专科" in normalized_name or "高等专科学校" in normalized_name:
            return "高职专科"
        if any(token in normalized_name for token in ["University", "College", "大学"]):
            return "普通本科"
        if "学院" in normalized_name:
            return "普通本科"
        return "未知"

    @staticmethod
    def _filter_tags(values: list[str], whitelist: list[str]) -> list[str]:
        return [value for value in values if value in whitelist]
