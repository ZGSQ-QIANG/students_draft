from __future__ import annotations

from typing import Any

from app.services.dictionaries import BEHAVIOR_TAGS, CAPABILITY_TAGS, JOB_DIRECTION_TAGS, STUDENT_TYPES


class PortraitEngine:
    def build(self, payload: dict[str, Any]) -> dict[str, Any]:
        portrait = payload.get("portrait") or {}
        internships = payload.get("internships") or []
        projects = payload.get("projects") or []
        educations = payload.get("educations") or []
        capability_tags = list(dict.fromkeys(portrait.get("capability_tags") or self._derive_capability_tags(payload)))
        behavior_tags = list(dict.fromkeys(portrait.get("behavior_tags") or self._derive_behavior_tags(payload)))
        job_direction_tags = list(dict.fromkeys(portrait.get("job_direction_tags") or self._derive_job_tags(payload)))
        student_type = portrait.get("student_type") or self._derive_student_type(educations, internships, projects)
        strengths = portrait.get("strengths") or self._derive_strengths(payload)
        risks = portrait.get("risks_or_gaps") or self._derive_risks(payload)
        summary = portrait.get("portrait_summary") or self._build_summary(student_type, strengths, risks)
        return {
            "student_type": student_type if student_type in STUDENT_TYPES else "探索型",
            "capability_tags": [tag for tag in capability_tags if tag in CAPABILITY_TAGS],
            "behavior_tags": [tag for tag in behavior_tags if tag in BEHAVIOR_TAGS],
            "job_direction_tags": [tag for tag in job_direction_tags if tag in JOB_DIRECTION_TAGS],
            "strengths": strengths,
            "risks_or_gaps": risks,
            "portrait_summary": summary,
            "confidence_score": portrait.get("confidence_score") or 0.72,
            "evidence_json": self._build_evidence(payload),
        }

    def _derive_student_type(self, educations: list[dict[str, Any]], internships: list[dict[str, Any]], projects: list[dict[str, Any]]) -> str:
        strong_academic = any((item.get("gpa_normalized") or 0) >= 3.5 for item in educations)
        strong_practice = len(internships) + len(projects) >= 3
        if strong_academic and strong_practice:
            return "复合型"
        if strong_practice:
            return "实践型"
        if strong_academic:
            return "学术型"
        return "探索型"

    def _derive_capability_tags(self, payload: dict[str, Any]) -> list[str]:
        tags: list[str] = []
        skill_names = " ".join(skill.get("skill_name", "") for skill in payload.get("skills") or [])
        all_text = " ".join(
            [
                " ".join(item.get("description_raw", "") for item in payload.get("internships") or []),
                " ".join(item.get("background", "") or "" for item in payload.get("projects") or []),
            ]
        )
        if any(token.lower() in skill_names.lower() for token in ["Python", "SQL", "Tableau", "Excel"]):
            tags.append("数据分析")
        if any(token.lower() in skill_names.lower() for token in ["Java", "C++", "Python"]):
            tags.append("技术实现")
        if "原型" in all_text or "Axure" in skill_names or "Figma" in skill_names:
            tags.append("原型设计")
        if any(token in all_text for token in ["组织", "协调", "推进", "沟通"]):
            tags.append("组织协调")
        if any(token in all_text for token in ["运营", "活动", "内容"]):
            tags.append("业务运营")
        return tags or ["组织协调"]

    def _derive_behavior_tags(self, payload: dict[str, Any]) -> list[str]:
        tags: list[str] = []
        total = len(payload.get("internships") or []) + len(payload.get("projects") or [])
        if total >= 2:
            tags.append("经历连续")
        text = " ".join(
            [
                " ".join(item.get("description_raw", "") for item in payload.get("internships") or []),
                " ".join(item.get("background", "") or "" for item in payload.get("projects") or []),
            ]
        )
        if any(token in text for token in ["主导", "负责", "发起", "组织"]):
            tags.append("主动性较强")
        if any(token in text for token in ["提升", "增长", "%", "上线", "完成"]):
            tags.append("结果导向")
        if len(set(payload.get("portrait", {}).get("job_direction_tags", []))) <= 1 and total > 0:
            tags.append("方向聚焦")
        return tags or ["成长性较好"]

    def _derive_job_tags(self, payload: dict[str, Any]) -> list[str]:
        tags: list[str] = []
        skill_names = " ".join(skill.get("skill_name", "") for skill in payload.get("skills") or []).lower()
        internship_text = " ".join(item.get("description_raw", "") for item in payload.get("internships") or []).lower()
        if any(token in skill_names for token in ["python", "java", "c++"]):
            tags.append("开发")
        if any(token in skill_names for token in ["sql", "tableau", "excel", "power bi"]):
            tags.append("数据分析")
        if any(token in internship_text for token in ["产品", "需求", "原型"]):
            tags.append("产品")
        if any(token in internship_text for token in ["运营", "活动", "用户"]):
            tags.append("运营")
        return tags or ["职能"]

    @staticmethod
    def _derive_strengths(payload: dict[str, Any]) -> list[str]:
        strengths = []
        if payload.get("internships"):
            strengths.append("具备实践经历，能够从简历中看到一定的业务或项目落地证据。")
        if payload.get("projects"):
            strengths.append("项目经历较完整，能够体现阶段性产出与角色承担。")
        if payload.get("educations") and any((edu.get("gpa_normalized") or 0) >= 3.2 for edu in payload["educations"]):
            strengths.append("教育背景信息较完整，学业基础相对稳定。")
        return strengths or ["当前简历已体现出一定的成长潜力。"]

    @staticmethod
    def _derive_risks(payload: dict[str, Any]) -> list[str]:
        risks = []
        if not payload.get("internships"):
            risks.append("缺少明确的实习经历，实践能力仍需更多证据支撑。")
        if not payload.get("projects"):
            risks.append("项目经历较少，难以完整评估复杂任务的落地能力。")
        metric_count = sum(len(item.get("metrics") or []) for item in payload.get("internships") or []) + sum(
            len(item.get("metrics") or []) for item in payload.get("projects") or []
        )
        if metric_count == 0:
            risks.append("量化成果较少，结果导向证据仍不够充分。")
        return risks or ["当前判断主要基于简历文本，仍需结合面试进一步校验。"]

    @staticmethod
    def _build_summary(student_type: str, strengths: list[str], risks: list[str]) -> str:
        overall = f"该学生当前更接近{student_type}画像，判断基于教育背景、项目经历与实习信息综合形成。"
        advantages = f"核心优势主要体现在：{'；'.join(strengths[:2])}"
        gaps = f"当前缺口或待验证点包括：{'；'.join(risks[:2])}"
        return "\n".join([overall, advantages, gaps])

    @staticmethod
    def _build_evidence(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "internship_count": len(payload.get("internships") or []),
            "project_count": len(payload.get("projects") or []),
            "skill_names": [item.get("skill_name") for item in payload.get("skills") or []],
        }

