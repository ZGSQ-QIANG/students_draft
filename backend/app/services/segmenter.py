from __future__ import annotations

import re

from app.services.dictionaries import SECTION_KEYWORDS


class SectionSegmenter:
    def segment(self, raw_text: str) -> dict[str, list[str]]:
        cleaned = raw_text.replace("\r", "\n")
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        if not lines:
            return {"basic_info": [], "education": [], "internship": [], "project": [], "awards": [], "skills": [], "self_eval": []}

        sections: dict[str, list[str]] = {key: [] for key in SECTION_KEYWORDS}
        current = "basic_info"
        bucket: list[str] = []

        def flush(target: str, content: list[str]) -> None:
            if content:
                sections[target].append("\n".join(content).strip())

        for line in lines:
            matched = self._match_section(line)
            if matched:
                flush(current, bucket)
                bucket = []
                current = matched
                continue
            bucket.append(line)
        flush(current, bucket)

        if not any(sections.values()):
            return {"basic_info": [cleaned], "education": [], "internship": [], "project": [], "awards": [], "skills": [], "self_eval": []}
        return sections

    def _match_section(self, line: str) -> str | None:
        normalized = line.lower()
        ordered = sorted(
            ((name, keyword) for name, keywords in SECTION_KEYWORDS.items() for keyword in keywords),
            key=lambda item: len(item[1]),
            reverse=True,
        )
        for name, keyword in ordered:
            if keyword.lower() in normalized:
                return name
        if re.fullmatch(r"(教育经历|实习经历|项目经历|技能证书|自我评价)", line):
            mapping = {
                "教育经历": "education",
                "实习经历": "internship",
                "项目经历": "project",
                "技能证书": "skills",
                "自我评价": "self_eval",
            }
            return mapping.get(line)
        return None
