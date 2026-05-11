from typing import Any

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin


class Student(TimestampMixin, Base):
    __tablename__ = "student"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_mode: Mapped[str] = mapped_column(String(32), default="student", index=True)
    dedup_fingerprint: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    dedup_status: Mapped[str] = mapped_column(String(32), default="resolved", index=True)
    display_name: Mapped[str | None] = mapped_column(String(100))
    school_name: Mapped[str | None] = mapped_column(String(255))
    major: Mapped[str | None] = mapped_column(String(255))
    graduation_date: Mapped[str | None] = mapped_column(String(32))

    resumes = relationship("Resume", back_populates="student")


class StudentBasicInfo(TimestampMixin, Base):
    __tablename__ = "student_basic_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str | None] = mapped_column(String(100))
    gender: Mapped[str | None] = mapped_column(String(16))
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(100))
    highest_degree: Mapped[str | None] = mapped_column(String(32))
    graduation_date: Mapped[str | None] = mapped_column(String(32))
    political_status: Mapped[str | None] = mapped_column(String(50))
    research_interest: Mapped[str | None] = mapped_column(Text)
    target_research_direction: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="basic_info")


class StudentEducation(TimestampMixin, Base):
    __tablename__ = "student_education"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    school_name: Mapped[str | None] = mapped_column(String(255))
    school_level: Mapped[str | None] = mapped_column(String(100))
    degree: Mapped[str | None] = mapped_column(String(32))
    major: Mapped[str | None] = mapped_column(String(255))
    minor: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[str | None] = mapped_column(String(32))
    end_date: Mapped[str | None] = mapped_column(String(32))
    gpa_raw: Mapped[str | None] = mapped_column(String(64))
    gpa_normalized: Mapped[float | None] = mapped_column(Float)
    rank_raw: Mapped[str | None] = mapped_column(String(64))
    rank_normalized: Mapped[float | None] = mapped_column(Float)
    core_courses: Mapped[list[str] | None] = mapped_column(JSON)
    scholarships: Mapped[list[str] | None] = mapped_column(JSON)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="educations")


class StudentInternship(TimestampMixin, Base):
    __tablename__ = "student_internship"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    company_name: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))
    job_title: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[str | None] = mapped_column(String(32))
    end_date: Mapped[str | None] = mapped_column(String(32))
    duration_months: Mapped[int | None] = mapped_column(Integer)
    responsibilities: Mapped[list[str] | None] = mapped_column(JSON)
    actions: Mapped[list[str] | None] = mapped_column(JSON)
    results: Mapped[list[str] | None] = mapped_column(JSON)
    metrics: Mapped[list[str] | None] = mapped_column(JSON)
    tools_used: Mapped[list[str] | None] = mapped_column(JSON)
    skills_inferred: Mapped[list[str] | None] = mapped_column(JSON)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    description_raw: Mapped[str | None] = mapped_column(Text)

    resume = relationship("Resume", back_populates="internships")


class StudentProject(TimestampMixin, Base):
    __tablename__ = "student_project"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    project_name: Mapped[str | None] = mapped_column(String(255))
    project_type: Mapped[str | None] = mapped_column(String(100))
    role_name: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[str | None] = mapped_column(String(32))
    end_date: Mapped[str | None] = mapped_column(String(32))
    team_size: Mapped[int | None] = mapped_column(Integer)
    background: Mapped[str | None] = mapped_column(Text)
    responsibilities: Mapped[list[str] | None] = mapped_column(JSON)
    methods_or_tech: Mapped[list[str] | None] = mapped_column(JSON)
    deliverables: Mapped[list[str] | None] = mapped_column(JSON)
    results: Mapped[list[str] | None] = mapped_column(JSON)
    metrics: Mapped[list[str] | None] = mapped_column(JSON)
    skills_inferred: Mapped[list[str] | None] = mapped_column(JSON)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="projects")


class StudentAward(TimestampMixin, Base):
    __tablename__ = "student_award"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    award_name: Mapped[str | None] = mapped_column(String(255))
    award_type: Mapped[str | None] = mapped_column(String(100))
    award_level: Mapped[str | None] = mapped_column(String(100))
    award_date: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="awards")


class StudentPaper(TimestampMixin, Base):
    __tablename__ = "student_paper"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str | None] = mapped_column(String(100))
    publication_type: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str | None] = mapped_column(String(100))
    publish_date: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="papers")


class StudentPatent(TimestampMixin, Base):
    __tablename__ = "student_patent"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    patent_name: Mapped[str | None] = mapped_column(String(255))
    patent_type: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str | None] = mapped_column(String(100))
    application_date: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="patents")


class StudentCompetition(TimestampMixin, Base):
    __tablename__ = "student_competition"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    competition_name: Mapped[str | None] = mapped_column(String(255))
    award_level: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str | None] = mapped_column(String(100))
    competition_date: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="competitions")


class StudentSkill(TimestampMixin, Base):
    __tablename__ = "student_skill"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    skill_name: Mapped[str] = mapped_column(String(100))
    skill_category: Mapped[str | None] = mapped_column(String(100))
    proficiency_level: Mapped[str | None] = mapped_column(String(50))
    source_type: Mapped[str | None] = mapped_column(String(50))
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="skills")


class StudentPortrait(TimestampMixin, Base):
    __tablename__ = "student_portrait"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), unique=True)
    portrait_mode: Mapped[str | None] = mapped_column(String(32))
    student_type: Mapped[str | None] = mapped_column(String(100))
    capability_tags: Mapped[list[str] | None] = mapped_column(JSON)
    behavior_tags: Mapped[list[str] | None] = mapped_column(JSON)
    job_direction_tags: Mapped[list[str] | None] = mapped_column(JSON)
    research_direction_tags: Mapped[list[str] | None] = mapped_column(JSON)
    method_tags: Mapped[list[str] | None] = mapped_column(JSON)
    academic_potential_tags: Mapped[list[str] | None] = mapped_column(JSON)
    strengths: Mapped[list[str] | None] = mapped_column(JSON)
    risks_or_gaps: Mapped[list[str] | None] = mapped_column(JSON)
    portrait_summary: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="portrait")


class ResumeReviewVersion(TimestampMixin, Base):
    __tablename__ = "resume_review_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    editor: Mapped[str] = mapped_column(String(100))
    review_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    diff_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="review_versions")


class ExtractLog(TimestampMixin, Base):
    __tablename__ = "extract_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    stage_name: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    input_text: Mapped[str | None] = mapped_column(Text)
    output_text: Mapped[str | None] = mapped_column(Text)
    validate_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="success")
    error_message: Mapped[str | None] = mapped_column(Text)

    resume = relationship("Resume", back_populates="extract_logs")


class EmbeddingIndex(TimestampMixin, Base):
    __tablename__ = "embedding_index"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    section_id: Mapped[int | None] = mapped_column(ForeignKey("resume_section.id", ondelete="SET NULL"))
    doc_type: Mapped[str] = mapped_column(String(50), index=True)
    text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    embedding: Mapped[list[float] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="embeddings")


class StudentResumeChunk(TimestampMixin, Base):
    __tablename__ = "student_resume_chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    analysis_mode: Mapped[str] = mapped_column(String(32), default="student", index=True)
    chunk_type: Mapped[str] = mapped_column(String(50), index=True)
    source_table: Mapped[str] = mapped_column(String(64))
    source_row_id: Mapped[int | None] = mapped_column(Integer, index=True)
    chunk_order: Mapped[int] = mapped_column(Integer, default=0)
    content_text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    index_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)

    resume = relationship("Resume", back_populates="resume_chunks")


class StudentFacultyMatch(TimestampMixin, Base):
    __tablename__ = "student_faculty_match"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    faculty_id: Mapped[int | None] = mapped_column(Integer, index=True)
    direction_score: Mapped[float | None] = mapped_column(Float)
    method_score: Mapped[float | None] = mapped_column(Float)
    background_score: Mapped[float | None] = mapped_column(Float)
    potential_score: Mapped[float | None] = mapped_column(Float)
    total_score: Mapped[float | None] = mapped_column(Float)
    match_level: Mapped[str | None] = mapped_column(String(50))
    match_reason: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="faculty_matches")


class StudentJobMatch(TimestampMixin, Base):
    __tablename__ = "student_job_match"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int | None] = mapped_column(Integer, index=True)
    direction_score: Mapped[float | None] = mapped_column(Float)
    skill_score: Mapped[float | None] = mapped_column(Float)
    experience_score: Mapped[float | None] = mapped_column(Float)
    potential_score: Mapped[float | None] = mapped_column(Float)
    total_score: Mapped[float | None] = mapped_column(Float)
    match_level: Mapped[str | None] = mapped_column(String(50))
    match_reason: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    resume = relationship("Resume", back_populates="job_matches")
