from __future__ import annotations

import re

from app.services.dictionaries import COMPETITION_KEYWORDS, PAPER_KEYWORDS, PATENT_KEYWORDS, SECTION_KEYWORDS, SECTION_TYPES


class SectionSegmenter:
    def segment(self, raw_text: str) -> dict[str, list[str]]:
        cleaned = raw_text.replace("\r", "\n")
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        if not lines:
            return {key: [] for key in SECTION_TYPES}

        sections: dict[str, list[str]] = {key: [] for key in SECTION_TYPES}
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
            sections["basic_info"] = [cleaned]
            return sections
        return self._redistribute_sections(sections)

    def _match_section(self, line: str) -> str | None:
        normalized = line.lower()
        ordered = sorted(
            ((name, keyword) for name, keywords in SECTION_KEYWORDS.items() for keyword in keywords),
            key=lambda item: len(item[1]),
            reverse=True,
        )
        for name, keyword in ordered:
            if self._is_heading_match(normalized, keyword.lower()):
                return name
        if re.fullmatch(r"(教育经历|项目经历|实习经历|论文成果|专利成果|竞赛经历|获奖经历|证书|技能证书|自我评价)", line):
            mapping = {
                "教育经历": "education",
                "项目经历": "project",
                "实习经历": "internship",
                "论文成果": "paper",
                "专利成果": "patent",
                "竞赛经历": "competition",
                "获奖经历": "award",
                "证书": "certificate",
                "技能证书": "skills",
                "自我评价": "self_eval",
            }
            return mapping.get(line)
        return None

    def _redistribute_sections(self, sections: dict[str, list[str]]) -> dict[str, list[str]]:
        redistributed: dict[str, list[str]] = {key: [] for key in SECTION_TYPES}
        for section_type, items in sections.items():
            for item in items:
                target = self._infer_section_type(section_type, item)
                redistributed[target].append(item)
        return redistributed

    def _infer_section_type(self, current_type: str, content: str) -> str:
        lowered = content.lower()
        if current_type not in {"award", "certificate", "skills", "basic_info"}:
            return current_type
        if self._contains_keywords(lowered, PAPER_KEYWORDS):
            return "paper"
        if self._contains_keywords(lowered, PATENT_KEYWORDS):
            return "patent"
        if self._contains_keywords(lowered, COMPETITION_KEYWORDS):
            return "competition"
        if "证书" in content or any(token in lowered for token in ["cet", "toefl", "ielts", "教师资格", "计算机二级"]):
            return "certificate"
        if any(token in content for token in ["奖学金", "荣誉", "优秀学生", "三好学生", "一等奖", "二等奖", "三等奖"]):
            return "award"
        return current_type

    @staticmethod
    def _contains_keywords(text: str, keywords: list[str]) -> bool:
        return any(keyword.lower() in text for keyword in keywords)

    @staticmethod
    def _is_heading_match(line: str, keyword: str) -> bool:
        if len(line) > 20:
            return False
        normalized = re.sub(r"[:：\s]+$", "", line.strip())
        if normalized == keyword:
            return True
        return normalized == f"{keyword}栏目"
