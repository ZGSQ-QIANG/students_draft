from __future__ import annotations

import re
from typing import Any

from app.services.dictionaries import DEGREES, MAJOR_KEYWORDS, SCHOOL_KEYWORDS, SKILL_KEYWORD_MAP


class RuleExtractor:
    phone_pattern = re.compile(r"1[3-9]\d{9}")
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    date_pattern = re.compile(r"((?:20\d{2}|19\d{2})[./-]?(?:0?[1-9]|1[0-2])(?:[./-]?(?:0?[1-9]|[12]\d|3[01]))?)")
    gpa_pattern = re.compile(r"(GPA[:：]?\s*\d(?:\.\d+)?\s*/\s*(?:4(?:\.0)?|5(?:\.0)?|100))|(\d{2,3}\s*/\s*100)")
    name_pattern = re.compile(r"^[\u4e00-\u9fa5]{2,4}$")

    def extract(self, sections: dict[str, list[str]]) -> dict[str, Any]:
        joined = "\n".join(sum(sections.values(), []))
        basic_text = "\n".join(sections.get("basic_info", [])) or joined[:500]
        basic = self._extract_basic_info(basic_text, joined)
        education = [self._extract_education(text) for text in sections.get("education", []) if text.strip()]
        internships = [self._extract_experience(text, "internship") for text in sections.get("internship", []) if text.strip()]
        projects = [self._extract_experience(text, "project") for text in sections.get("project", []) if text.strip()]
        awards = [self._extract_award(text) for text in sections.get("awards", []) if text.strip()]
        skills = self._extract_skills("\n".join(sections.get("skills", [])) + "\n" + joined)
        return {
            "basic_info": basic,
            "educations": education,
            "internships": internships,
            "projects": projects,
            "awards": awards,
            "skills": skills,
        }

    def _extract_basic_info(self, basic_text: str, full_text: str) -> dict[str, Any]:
        lines = [line.strip() for line in basic_text.splitlines() if line.strip()]
        name = next((line for line in lines[:3] if self.name_pattern.match(line)), None)
        phone = self._first_match(self.phone_pattern, full_text)
        email = self._first_match(self.email_pattern, full_text)
        highest_degree = next((degree for degree in DEGREES if degree in full_text), None)
        graduation_date = self._guess_graduation(full_text)
        city = next((line for line in lines if any(token in line for token in ["市", "省", "北京", "上海", "广州", "深圳"])), None)
        return {
            "name": name,
            "phone": phone,
            "email": email,
            "highest_degree": highest_degree,
            "graduation_date": graduation_date,
            "city": city,
            "evidence_json": {"source": "rule", "basic_text": basic_text[:300]},
        }

    def _extract_education(self, text: str) -> dict[str, Any]:
        school_name = next((token.strip() for token in text.split() if any(key in token for key in SCHOOL_KEYWORDS)), None)
        if not school_name:
            school_name = next((line for line in text.splitlines() if any(key in line for key in SCHOOL_KEYWORDS)), None)
        degree = next((degree for degree in DEGREES if degree in text), None)
        major = next((keyword for keyword in MAJOR_KEYWORDS if keyword in text), None)
        dates = self.date_pattern.findall(text)
        flat_dates = [item if isinstance(item, str) else next((x for x in item if x), "") for item in dates]
        gpa_raw = self._extract_gpa(text)
        return {
            "school_name": school_name,
            "degree": degree,
            "major": major,
            "start_date": flat_dates[0] if len(flat_dates) > 0 else None,
            "end_date": flat_dates[1] if len(flat_dates) > 1 else None,
            "gpa_raw": gpa_raw,
            "evidence_json": {"source": "rule", "text": text[:400]},
        }

    def _extract_experience(self, text: str, kind: str) -> dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        title = lines[0] if lines else None
        dates = self.date_pattern.findall(text)
        flat_dates = [item if isinstance(item, str) else next((x for x in item if x), "") for item in dates]
        metrics = re.findall(r"(提升|增长|完成|支撑|负责)[^。\n]{0,25}\d+%?", text)
        base = {
            "start_date": flat_dates[0] if len(flat_dates) > 0 else None,
            "end_date": flat_dates[1] if len(flat_dates) > 1 else None,
            "metrics": metrics,
            "evidence_json": {"source": "rule", "text": text[:400]},
        }
        if kind == "internship":
            company = lines[0] if lines else None
            job_title = lines[1] if len(lines) > 1 and len(lines[1]) < 30 else None
            base.update({"company_name": company, "job_title": job_title, "description_raw": text})
        else:
            base.update(
                {
                    "project_name": title,
                    "role_name": lines[1] if len(lines) > 1 and len(lines[1]) < 30 else None,
                    "background": text,
                }
            )
        return base

    def _extract_award(self, text: str) -> dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        award_name = lines[0] if lines else text[:50]
        level = next((level for level in ["国家级", "省级", "市级", "校级", "一等奖", "二等奖", "三等奖"] if level in text), None)
        dates = self.date_pattern.findall(text)
        flat_dates = [item if isinstance(item, str) else next((x for x in item if x), "") for item in dates]
        return {
            "award_name": award_name,
            "award_level": level,
            "award_date": flat_dates[0] if flat_dates else None,
            "description": text,
            "evidence_json": {"source": "rule", "text": text[:300]},
        }

    def _extract_skills(self, text: str) -> list[dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        lower = text.lower()
        for keyword, (display, category) in SKILL_KEYWORD_MAP.items():
            if keyword in lower:
                found[display] = {
                    "skill_name": display,
                    "skill_category": category,
                    "source_type": "rule",
                    "evidence_json": {"keyword": keyword},
                }
        return list(found.values())

    def _extract_gpa(self, text: str) -> str | None:
        match = self.gpa_pattern.search(text)
        if not match:
            return None
        return next(group for group in match.groups() if group)

    def _guess_graduation(self, text: str) -> str | None:
        matches = self.date_pattern.findall(text)
        flat_dates = [item if isinstance(item, str) else next((x for x in item if x), "") for item in matches]
        if not flat_dates:
            return None
        return flat_dates[-1]

    @staticmethod
    def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
        match = pattern.search(text)
        return match.group(0) if match else None
