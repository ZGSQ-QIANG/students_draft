from __future__ import annotations

from typing import Any

from app.services.dictionaries import (
    ACADEMIC_POTENTIAL_TAGS,
    BEHAVIOR_TAGS,
    CAPABILITY_TAGS,
    JOB_DIRECTION_TAGS,
    METHOD_TAGS,
    RESEARCH_DIRECTION_TAGS,
    STUDENT_MODE,
    STUDENT_TYPES,
)


class StudentPortraitEngine:
    portrait_mode = STUDENT_MODE

    def build(self, payload: dict[str, Any]) -> dict[str, Any]:
        portrait = payload.get("portrait") or {}
        student_type = portrait.get("student_type") or self._derive_student_type(payload)
        strengths = portrait.get("strengths") or self._derive_strengths(payload)
        risks = portrait.get("risks_or_gaps") or self._derive_risks(payload)
        research_direction_tags = self._unique(portrait.get("research_direction_tags") or self._derive_research_directions(payload))
        method_tags = self._unique(portrait.get("method_tags") or self._derive_method_tags(payload))
        academic_potential_tags = self._unique(portrait.get("academic_potential_tags") or self._derive_academic_potential(payload))
        capability_tags = self._unique(portrait.get("capability_tags") or self._derive_capability_tags(payload))
        behavior_tags = self._unique(portrait.get("behavior_tags") or self._derive_behavior_tags(payload))
        job_direction_tags = self._unique(portrait.get("job_direction_tags") or self._derive_job_tags(payload))
        return {
            "portrait_mode": self.portrait_mode,
            "student_type": student_type if student_type in STUDENT_TYPES else "探索型",
            "capability_tags": [tag for tag in capability_tags if tag in CAPABILITY_TAGS],
            "behavior_tags": [tag for tag in behavior_tags if tag in BEHAVIOR_TAGS],
            "job_direction_tags": [tag for tag in job_direction_tags if tag in JOB_DIRECTION_TAGS],
            "research_direction_tags": [tag for tag in research_direction_tags if tag in RESEARCH_DIRECTION_TAGS],
            "method_tags": [tag for tag in method_tags if tag in METHOD_TAGS],
            "academic_potential_tags": [tag for tag in academic_potential_tags if tag in ACADEMIC_POTENTIAL_TAGS],
            "strengths": strengths,
            "risks_or_gaps": risks,
            "portrait_summary": portrait.get("portrait_summary") or self._build_summary(student_type, strengths, risks),
            "confidence_score": portrait.get("confidence_score") or 0.73,
            "evidence_json": self._build_evidence(payload),
        }

    def _derive_student_type(self, payload: dict[str, Any]) -> str:
        educations = payload.get("educations") or []
        internships = payload.get("internships") or []
        projects = payload.get("projects") or []
        outputs = len(payload.get("papers") or []) + len(payload.get("patents") or []) + len(payload.get("competitions") or [])
        strong_academic = any((item.get("gpa_normalized") or 0) >= 3.5 for item in educations) or outputs >= 2
        strong_practice = len(internships) + len(projects) >= 3
        if strong_academic and strong_practice:
            return "复合型"
        if strong_academic:
            return "学术型"
        if strong_practice:
            return "实践型"
        return "探索型"

    def _derive_capability_tags(self, payload: dict[str, Any]) -> list[str]:
        skill_names = " ".join(skill.get("skill_name", "") for skill in payload.get("skills") or [])
        all_text = self._joined_text(payload)
        tags = []
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
        total = len(payload.get("internships") or []) + len(payload.get("projects") or [])
        text = self._joined_text(payload)
        tags = []
        if total >= 2:
            tags.append("经历连续")
        if any(token in text for token in ["主导", "负责", "发起", "组织"]):
            tags.append("主动性较强")
        if any(token in text for token in ["提升", "增长", "%", "上线", "完成"]):
            tags.append("结果导向")
        if len(self._derive_job_tags(payload)) <= 1 and total > 0:
            tags.append("方向聚焦")
        return tags or ["成长性较好"]

    def _derive_job_tags(self, payload: dict[str, Any]) -> list[str]:
        skill_names = " ".join(skill.get("skill_name", "") for skill in payload.get("skills") or []).lower()
        text = self._joined_text(payload).lower()
        tags = []
        if any(token in skill_names for token in ["python", "java", "c++"]):
            tags.append("开发")
        if any(token in skill_names for token in ["sql", "tableau", "excel", "power bi"]):
            tags.append("数据分析")
        if any(token in text for token in ["产品", "需求", "原型"]):
            tags.append("产品")
        if any(token in text for token in ["运营", "活动", "用户"]):
            tags.append("运营")
        return tags or ["职能"]

    def _derive_research_directions(self, payload: dict[str, Any]) -> list[str]:
        text = self._joined_text(payload).lower()
        mapping = {
            "人工智能": ["人工智能", "机器学习", "ai"],
            "数据挖掘": ["数据挖掘", "数据分析", "商业分析"],
            "自然语言处理": ["自然语言", "nlp", "文本分析"],
            "计算机视觉": ["视觉", "图像", "cv"],
            "推荐系统": ["推荐", "用户画像", "召回"],
            "信息系统": ["信息系统", "系统设计", "管理信息系统"],
            "金融科技": ["金融科技", "金融工程", "量化"],
            "教育技术": ["教育技术", "教育数据", "学习分析"],
            "管理研究": ["管理学", "组织", "战略", "人力资源"],
            "传播与媒介": ["传播", "媒介", "新闻", "舆情"],
        }
        return [tag for tag, keywords in mapping.items() if any(keyword in text for keyword in keywords)] or ["信息系统"]

    def _derive_method_tags(self, payload: dict[str, Any]) -> list[str]:
        text = self._joined_text(payload).lower()
        skills = " ".join(skill.get("skill_name", "") for skill in payload.get("skills") or []).lower()
        tags = []
        if any(keyword in text for keyword in ["实验", "ab测试", "对照组"]):
            tags.append("实验设计")
        if any(keyword in text for keyword in ["文献", "综述", "阅读"]):
            tags.append("文献综述")
        if any(keyword in text for keyword in ["回归", "统计", "spss", "stata"]) or "sql" in skills:
            tags.append("统计分析")
        if any(keyword in text for keyword in ["问卷", "访谈", "调研"]):
            tags.append("问卷调研")
        if any(keyword in text for keyword in ["建模", "仿真", "优化"]):
            tags.append("建模仿真")
        if any(keyword in skills for keyword in ["python", "java", "c++"]):
            tags.append("编程实现")
        if any(keyword in skills for keyword in ["sql", "excel", "tableau", "power bi"]):
            tags.append("数据分析")
        if any(keyword in text for keyword in ["深度学习", "神经网络", "pytorch", "tensorflow"]):
            tags.append("深度学习")
        return tags or ["文献综述"]

    def _derive_academic_potential(self, payload: dict[str, Any]) -> list[str]:
        basic_info = payload.get("basic_info") or {}
        educations = payload.get("educations") or []
        tags = []
        if any((item.get("gpa_normalized") or 0) >= 3.5 for item in educations):
            tags.append("学术基础扎实")
        if basic_info.get("research_interest") or basic_info.get("target_research_direction"):
            tags.append("研究兴趣明确")
        if len(self._derive_method_tags(payload)) >= 2:
            tags.append("方法基础较好")
        if payload.get("papers") or payload.get("patents") or payload.get("competitions"):
            tags.append("科研潜力较强")
        if any(item.get("description") for item in payload.get("papers") or []):
            tags.append("学术表达较完整")
        return tags or ["研究兴趣明确"]

    @staticmethod
    def _derive_strengths(payload: dict[str, Any]) -> list[str]:
        strengths = []
        if payload.get("projects"):
            strengths.append("项目经历较完整，能够体现阶段性产出与角色承担。")
        if payload.get("internships"):
            strengths.append("具备实践经历，能够从简历中看到一定的业务或项目落地证据。")
        if payload.get("papers") or payload.get("patents") or payload.get("competitions"):
            strengths.append("具备论文、专利或竞赛等成果线索，能体现一定探索和产出能力。")
        if payload.get("educations") and any((edu.get("gpa_normalized") or 0) >= 3.2 for edu in payload["educations"]):
            strengths.append("教育背景信息较完整，学业基础相对稳定。")
        return strengths or ["当前简历已体现出一定的成长潜力。"]

    @staticmethod
    def _derive_risks(payload: dict[str, Any]) -> list[str]:
        risks = []
        if not payload.get("projects"):
            risks.append("项目经历较少，难以完整评估复杂任务的落地能力。")
        if not payload.get("internships"):
            risks.append("缺少明确的实习经历，实践能力仍需更多证据支撑。")
        if not payload.get("papers") and not payload.get("patents") and not payload.get("competitions"):
            risks.append("论文、专利或竞赛等外显成果较少，综合佐证维度仍有限。")
        return risks or ["当前判断主要基于简历文本，仍需结合后续沟通进一步验证。"]

    @staticmethod
    def _build_summary(student_type: str, strengths: list[str], risks: list[str]) -> str:
        return "\n".join(
            [
                f"该学生当前更接近{student_type}画像，判断基于教育背景、项目经历、成果经历与技能信息综合形成。",
                f"核心优势主要体现在：{'；'.join(strengths[:2])}",
                f"当前缺口或待验证点包括：{'；'.join(risks[:2])}",
            ]
        )

    @staticmethod
    def _build_evidence(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "portrait_mode": STUDENT_MODE,
            "internship_count": len(payload.get("internships") or []),
            "project_count": len(payload.get("projects") or []),
            "paper_count": len(payload.get("papers") or []),
            "patent_count": len(payload.get("patents") or []),
            "competition_count": len(payload.get("competitions") or []),
            "skill_names": [item.get("skill_name") for item in payload.get("skills") or []],
        }

    @staticmethod
    def _joined_text(payload: dict[str, Any]) -> str:
        basic_info = payload.get("basic_info") or {}
        parts = [
            basic_info.get("research_interest") or "",
            basic_info.get("target_research_direction") or "",
            " ".join(item.get("description_raw") or "" for item in payload.get("internships") or []),
            " ".join(item.get("background") or "" for item in payload.get("projects") or []),
            " ".join(item.get("description") or "" for item in payload.get("papers") or []),
            " ".join(item.get("description") or "" for item in payload.get("patents") or []),
            " ".join(item.get("description") or "" for item in payload.get("competitions") or []),
        ]
        return " ".join(part for part in parts if part)

    @staticmethod
    def _unique(values: list[str] | None) -> list[str]:
        return list(dict.fromkeys(values or []))


def build_portrait_engine(mode: str | None = None) -> StudentPortraitEngine:
    return StudentPortraitEngine()


PortraitEngine = StudentPortraitEngine
CareerPortraitEngine = StudentPortraitEngine
AcademicPortraitEngine = StudentPortraitEngine
