from __future__ import annotations

import re
from hashlib import sha1

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Resume, Student
from app.services.dictionaries import STUDENT_MODE


class StudentIdentityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def resolve_resume(self, resume: Resume) -> Student:
        fingerprint, status, display = self._build_fingerprint(resume)
        student = self.db.execute(select(Student).where(Student.dedup_fingerprint == fingerprint)).scalar_one_or_none()
        if student is None:
            student = Student(
                analysis_mode=STUDENT_MODE,
                dedup_fingerprint=fingerprint,
                dedup_status=status,
                display_name=display["display_name"],
                school_name=display["school_name"],
                major=display["major"],
                graduation_date=display["graduation_date"],
            )
            self.db.add(student)
            self.db.flush()
        else:
            student.analysis_mode = STUDENT_MODE
            student.dedup_status = status
            student.display_name = display["display_name"] or student.display_name
            student.school_name = display["school_name"] or student.school_name
            student.major = display["major"] or student.major
            student.graduation_date = display["graduation_date"] or student.graduation_date

        resume.student_id = student.id
        resume.dedup_fingerprint = fingerprint
        resume.duplicate_status = status
        self.db.flush()
        self._refresh_primary(student.id)
        return student

    def _refresh_primary(self, student_id: int) -> None:
        resumes = (
            self.db.execute(
                select(Resume)
                .where(Resume.student_id == student_id)
                .options(selectinload(Resume.basic_info), selectinload(Resume.educations))
                .order_by(Resume.created_at.desc(), Resume.id.desc())
            )
            .scalars()
            .all()
        )
        primary_id = None
        for resume in resumes:
            if self._is_effective_resume(resume):
                primary_id = resume.id
                break
        if primary_id is None and resumes:
            primary_id = resumes[0].id

        for resume in resumes:
            resume.is_primary = resume.id == primary_id

    @staticmethod
    def _is_effective_resume(resume: Resume) -> bool:
        return resume.parse_status != "failed" and resume.extract_status != "failed"

    def _build_fingerprint(self, resume: Resume) -> tuple[str, str, dict[str, str | None]]:
        basic_info = resume.basic_info
        education = resume.educations[0] if resume.educations else None
        display = {
            "display_name": basic_info.name if basic_info else None,
            "school_name": education.school_name if education else None,
            "major": education.major if education else None,
            "graduation_date": basic_info.graduation_date if basic_info else None,
        }
        parts = [
            self._normalize_text(display["display_name"]),
            self._normalize_text(display["school_name"]),
            self._normalize_text(display["major"]),
            self._normalize_text(display["graduation_date"]),
        ]
        if all(parts):
            return "|".join(parts), "resolved", display
        fallback = sha1(f"resume:{resume.id}".encode("utf-8")).hexdigest()
        return f"resume-only|{fallback}", "insufficient_fields", display

    @staticmethod
    def _normalize_text(value: str | None) -> str:
        if not value:
            return ""
        text = value.strip().lower()
        text = text.replace("（", "(").replace("）", ")")
        text = re.sub(r"\s+", "", text)
        return text
