from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin


class Resume(TimestampMixin, Base):
    __tablename__ = "resume"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("student.id", ondelete="SET NULL"), index=True)
    batch_id: Mapped[str | None] = mapped_column(String(64), index=True)
    source_file_name: Mapped[str] = mapped_column(String(255))
    source_file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(32))
    analysis_mode: Mapped[str] = mapped_column(String(32), default="student", index=True)
    analysis_status: Mapped[str] = mapped_column(String(32), default="uploaded")
    parse_status: Mapped[str] = mapped_column(String(32), default="uploaded")
    extract_status: Mapped[str] = mapped_column(String(32), default="uploaded")
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    raw_text: Mapped[str | None] = mapped_column(Text)
    ocr_text: Mapped[str | None] = mapped_column(Text)
    page_texts: Mapped[list[str] | None] = mapped_column(JSON)
    section_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    last_error_stage: Mapped[str | None] = mapped_column(String(64))
    last_error_message: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(default=True, index=True)
    dedup_fingerprint: Mapped[str | None] = mapped_column(String(255), index=True)
    duplicate_status: Mapped[str | None] = mapped_column(String(32), default="pending", index=True)

    student = relationship("Student", back_populates="resumes")
    sections = relationship("ResumeSection", back_populates="resume", cascade="all, delete-orphan")
    basic_info = relationship("StudentBasicInfo", back_populates="resume", uselist=False, cascade="all, delete-orphan")
    educations = relationship("StudentEducation", back_populates="resume", cascade="all, delete-orphan")
    internships = relationship("StudentInternship", back_populates="resume", cascade="all, delete-orphan")
    projects = relationship("StudentProject", back_populates="resume", cascade="all, delete-orphan")
    awards = relationship("StudentAward", back_populates="resume", cascade="all, delete-orphan")
    papers = relationship("StudentPaper", back_populates="resume", cascade="all, delete-orphan")
    patents = relationship("StudentPatent", back_populates="resume", cascade="all, delete-orphan")
    competitions = relationship("StudentCompetition", back_populates="resume", cascade="all, delete-orphan")
    skills = relationship("StudentSkill", back_populates="resume", cascade="all, delete-orphan")
    portrait = relationship("StudentPortrait", back_populates="resume", uselist=False, cascade="all, delete-orphan")
    review_versions = relationship("ResumeReviewVersion", back_populates="resume", cascade="all, delete-orphan")
    extract_logs = relationship("ExtractLog", back_populates="resume", cascade="all, delete-orphan")
    embeddings = relationship("EmbeddingIndex", back_populates="resume", cascade="all, delete-orphan")
    resume_chunks = relationship("StudentResumeChunk", back_populates="resume", cascade="all, delete-orphan")
    faculty_matches = relationship("StudentFacultyMatch", back_populates="resume", cascade="all, delete-orphan")
    job_matches = relationship("StudentJobMatch", back_populates="resume", cascade="all, delete-orphan")


class ResumeSection(TimestampMixin, Base):
    __tablename__ = "resume_section"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    section_type: Mapped[str] = mapped_column(String(64), index=True)
    page_no: Mapped[int | None] = mapped_column(Integer)
    order_no: Mapped[int] = mapped_column(Integer, default=0)
    raw_content: Mapped[str] = mapped_column(Text)
    normalized_content: Mapped[str | None] = mapped_column(Text)

    resume = relationship("Resume", back_populates="sections")
