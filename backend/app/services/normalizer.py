from __future__ import annotations

import re
from typing import Any

from app.services.dictionaries import BEHAVIOR_TAGS, CAPABILITY_TAGS, DEGREES, JOB_DIRECTION_TAGS


class Normalizer:
    def normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        basic = payload.get("basic_info") or {}
        if basic.get("highest_degree") not in DEGREES:
            basic["highest_degree"] = self._normalize_degree(basic.get("highest_degree"))
        for education in payload.get("educations", []):
            education["degree"] = self._normalize_degree(education.get("degree"))
            education["gpa_normalized"] = self._normalize_gpa(education.get("gpa_raw"))
        portrait = payload.get("portrait") or {}
        portrait["capability_tags"] = self._filter_tags(portrait.get("capability_tags", []), CAPABILITY_TAGS)
        portrait["behavior_tags"] = self._filter_tags(portrait.get("behavior_tags", []), BEHAVIOR_TAGS)
        portrait["job_direction_tags"] = self._filter_tags(portrait.get("job_direction_tags", []), JOB_DIRECTION_TAGS)
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
    def _filter_tags(values: list[str], whitelist: list[str]) -> list[str]:
        return [value for value in values if value in whitelist]

