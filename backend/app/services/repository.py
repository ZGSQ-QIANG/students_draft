from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    EmbeddingIndex,
    Resume,
    ResumeReviewVersion,
    ResumeSection,
    StudentAward,
    StudentBasicInfo,
    StudentEducation,
    StudentInternship,
    StudentPortrait,
    StudentProject,
    StudentSkill,
)


class ResumeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_resume(self, *, batch_id: str, file_name: str, file_path: str, file_type: str) -> Resume:
        resume = Resume(
            batch_id=batch_id,
            source_file_name=file_name,
            source_file_path=file_path,
            file_type=file_type,
            parse_status="uploaded",
            extract_status="uploaded",
        )
        self.db.add(resume)
        self.db.flush()
        return resume

    def replace_sections(self, resume: Resume, sections: list[dict[str, Any]]) -> None:
        resume.sections.clear()
        for section in sections:
            resume.sections.append(ResumeSection(**section))

    def replace_structured_data(self, resume: Resume, payload: dict[str, Any]) -> None:
        def sanitize(model_cls: type, data: dict[str, Any]) -> dict[str, Any]:
            allowed = {column.name for column in model_cls.__table__.columns} - {"id", "resume_id", "created_at", "updated_at"}
            return {key: value for key, value in data.items() if key in allowed}

        def upsert_single(rel_name: str, model_cls: type, data: dict[str, Any] | None) -> None:
            current_obj = getattr(resume, rel_name)
            if not data:
                setattr(resume, rel_name, None)
                return

            clean = sanitize(model_cls, data)
            if current_obj is None:
                setattr(resume, rel_name, model_cls(**clean))
                return

            for key, value in clean.items():
                setattr(current_obj, key, value)

        upsert_single("basic_info", StudentBasicInfo, payload.get("basic_info"))

        resume.educations = [StudentEducation(**sanitize(StudentEducation, item)) for item in payload.get("educations", [])]
        resume.internships = [StudentInternship(**sanitize(StudentInternship, item)) for item in payload.get("internships", [])]
        resume.projects = [StudentProject(**sanitize(StudentProject, item)) for item in payload.get("projects", [])]
        resume.awards = [StudentAward(**sanitize(StudentAward, item)) for item in payload.get("awards", [])]
        resume.skills = [StudentSkill(**sanitize(StudentSkill, item)) for item in payload.get("skills", [])]
        upsert_single("portrait", StudentPortrait, payload.get("portrait"))

    def replace_embeddings(self, resume: Resume, items: list[dict[str, Any]]) -> None:
        resume.embeddings = [EmbeddingIndex(**item) for item in items]

    def create_review_version(self, resume: Resume, payload: dict[str, Any], editor: str) -> ResumeReviewVersion:
        review = ResumeReviewVersion(
            resume_id=resume.id,
            version_no=resume.current_version + 1,
            editor=editor,
            review_payload=payload,
            diff_payload={},
        )
        resume.current_version += 1
        self.db.add(review)
        return review
