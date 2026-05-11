from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models import Resume, ResumeSection
from app.services.dictionaries import STUDENT_MODE


@dataclass
class ChunkPayload:
    analysis_mode: str
    chunk_type: str
    source_table: str
    source_row_id: int | None
    chunk_order: int
    content_text: str
    metadata_json: dict[str, Any]


class ChunkBuilder:
    def build(self, resume: Resume) -> list[ChunkPayload]:
        metadata = self._base_metadata(resume)
        chunks: list[ChunkPayload] = []
        order = 0

        for education in resume.educations:
            text = self._compose_text(
                education.school_name,
                education.degree,
                education.major,
                self._join_list(education.core_courses, prefix="核心课程"),
                self._join_list(education.scholarships, prefix="奖学金"),
                self._range_text(education.start_date, education.end_date),
                education.gpa_raw and f"GPA {education.gpa_raw}",
            )
            order = self._append_chunk(
                chunks,
                STUDENT_MODE,
                "education",
                "student_education",
                education.id,
                order,
                text,
                metadata,
            )

        for project in resume.projects:
            text = self._compose_text(
                project.project_name,
                project.role_name and f"角色 {project.role_name}",
                project.background,
                self._join_list(project.responsibilities, prefix="职责"),
                self._join_list(project.methods_or_tech, prefix="方法/技术"),
                self._join_list(project.results, prefix="结果"),
                self._join_list(project.metrics, prefix="指标"),
                self._range_text(project.start_date, project.end_date),
            )
            order = self._append_chunk(
                chunks,
                STUDENT_MODE,
                "project",
                "student_project",
                project.id,
                order,
                text,
                metadata,
            )

        for internship in resume.internships:
            text = self._compose_text(
                internship.company_name,
                internship.job_title and f"岗位 {internship.job_title}",
                internship.description_raw,
                self._join_list(internship.responsibilities, prefix="职责"),
                self._join_list(internship.actions, prefix="动作"),
                self._join_list(internship.results, prefix="结果"),
                self._join_list(internship.metrics, prefix="指标"),
                self._range_text(internship.start_date, internship.end_date),
            )
            order = self._append_chunk(
                chunks,
                STUDENT_MODE,
                "internship",
                "student_internship",
                internship.id,
                order,
                text,
                metadata,
            )

        for paper in resume.papers:
            text = self._compose_text(
                paper.title,
                paper.publication_type,
                paper.status,
                paper.role and f"角色 {paper.role}",
                paper.publish_date and f"时间 {paper.publish_date}",
                paper.description,
            )
            order = self._append_chunk(
                chunks,
                STUDENT_MODE,
                "paper",
                "student_paper",
                paper.id,
                order,
                text,
                metadata,
            )

        for patent in resume.patents:
            text = self._compose_text(
                patent.patent_name,
                patent.patent_type,
                patent.status,
                patent.role and f"角色 {patent.role}",
                patent.application_date and f"时间 {patent.application_date}",
                patent.description,
            )
            order = self._append_chunk(
                chunks,
                STUDENT_MODE,
                "patent",
                "student_patent",
                patent.id,
                order,
                text,
                metadata,
            )

        for competition in resume.competitions:
            text = self._compose_text(
                competition.competition_name,
                competition.award_level,
                competition.role and f"角色 {competition.role}",
                competition.competition_date and f"时间 {competition.competition_date}",
                competition.description,
            )
            order = self._append_chunk(
                chunks,
                STUDENT_MODE,
                "competition",
                "student_competition",
                competition.id,
                order,
                text,
                metadata,
            )

        for award in resume.awards:
            text = self._compose_text(
                award.award_name,
                award.award_type,
                award.award_level,
                award.award_date and f"时间 {award.award_date}",
                award.description,
            )
            order = self._append_chunk(
                chunks,
                STUDENT_MODE,
                "award",
                "student_award",
                award.id,
                order,
                text,
                metadata,
            )

        certificate_sections = sorted(
            [section for section in resume.sections if section.section_type == "certificate"],
            key=lambda item: item.order_no,
        )
        for section in certificate_sections:
            order = self._append_chunk(
                chunks,
                STUDENT_MODE,
                "certificate",
                "resume_section",
                section.id,
                order,
                section.raw_content,
                metadata,
            )

        return chunks

    def _base_metadata(self, resume: Resume) -> dict[str, Any]:
        basic_info = resume.basic_info
        education = resume.educations[0] if resume.educations else None
        portrait = resume.portrait
        metadata: dict[str, Any] = {
            "student_id": resume.student_id,
            "resume_id": resume.id,
            "analysis_mode": STUDENT_MODE,
            "student_name": basic_info.name if basic_info else None,
            "school_name": education.school_name if education else None,
            "major": education.major if education else None,
            "highest_degree": basic_info.highest_degree if basic_info else None,
            "student_type": portrait.student_type if portrait else None,
        }
        if portrait:
            metadata["research_direction_tags"] = portrait.research_direction_tags or []
            metadata["method_tags"] = portrait.method_tags or []
            metadata["academic_potential_tags"] = portrait.academic_potential_tags or []
            metadata["job_direction_tags"] = portrait.job_direction_tags or []
            metadata["capability_tags"] = portrait.capability_tags or []
            metadata["behavior_tags"] = portrait.behavior_tags or []
        return metadata

    def _append_chunk(
        self,
        chunks: list[ChunkPayload],
        analysis_mode: str,
        chunk_type: str,
        source_table: str,
        source_row_id: int | None,
        order: int,
        text: str | None,
        metadata: dict[str, Any],
    ) -> int:
        if not text or not text.strip():
            return order
        chunk_metadata = {**metadata, "chunk_type": chunk_type}
        chunks.append(
            ChunkPayload(
                analysis_mode=analysis_mode,
                chunk_type=chunk_type,
                source_table=source_table,
                source_row_id=source_row_id,
                chunk_order=order,
                content_text=text.strip(),
                metadata_json=chunk_metadata,
            )
        )
        return order + 1

    @staticmethod
    def _compose_text(*parts: Any) -> str:
        values = []
        for part in parts:
            if part is None:
                continue
            text = str(part).strip()
            if text:
                values.append(text)
        return "\n".join(values)

    @staticmethod
    def _join_list(items: list[str] | None, *, prefix: str) -> str | None:
        if not items:
            return None
        values = [item.strip() for item in items if item and item.strip()]
        if not values:
            return None
        return f"{prefix}：" + "；".join(values)

    @staticmethod
    def _range_text(start_date: str | None, end_date: str | None) -> str | None:
        if not start_date and not end_date:
            return None
        return f"时间 {start_date or ''} - {end_date or ''}".strip()
