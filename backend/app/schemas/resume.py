from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import EvidenceSpan, ORMModel


class ResumeUploadItem(BaseModel):
    resume_id: int
    file_name: str
    status: str
    analysis_mode: str


class ResumeListItem(ORMModel):
    id: int
    student_id: int | None = None
    batch_id: str | None
    source_file_name: str
    file_type: str
    student_name: str | None = None
    school_name: str | None = None
    major: str | None = None
    student_type: str | None = None
    analysis_mode: str
    analysis_status: str
    parse_status: str
    extract_status: str
    last_error_stage: str | None = None
    last_error_message: str | None = None
    current_version: int


class BasicInfoPayload(ORMModel):
    name: str | None = None
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    highest_degree: str | None = None
    graduation_date: str | None = None
    political_status: str | None = None
    research_interest: str | None = None
    target_research_direction: str | None = None
    evidence_json: dict[str, Any] | None = None


class EducationPayload(ORMModel):
    school_name: str | None = None
    school_level: str | None = None
    degree: str | None = None
    major: str | None = None
    minor: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa_raw: str | None = None
    gpa_normalized: float | None = None
    rank_raw: str | None = None
    rank_normalized: float | None = None
    core_courses: list[str] | None = None
    scholarships: list[str] | None = None
    evidence_json: dict[str, Any] | None = None


class InternshipPayload(ORMModel):
    company_name: str | None = None
    industry: str | None = None
    department: str | None = None
    job_title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_months: int | None = None
    responsibilities: list[str] | None = None
    actions: list[str] | None = None
    results: list[str] | None = None
    metrics: list[str] | None = None
    tools_used: list[str] | None = None
    skills_inferred: list[str] | None = None
    evidence_json: dict[str, Any] | None = None
    description_raw: str | None = None


class ProjectPayload(ORMModel):
    project_name: str | None = None
    project_type: str | None = None
    role_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    team_size: int | None = None
    background: str | None = None
    responsibilities: list[str] | None = None
    methods_or_tech: list[str] | None = None
    deliverables: list[str] | None = None
    results: list[str] | None = None
    metrics: list[str] | None = None
    skills_inferred: list[str] | None = None
    evidence_json: dict[str, Any] | None = None


class AwardPayload(ORMModel):
    award_name: str | None = None
    award_type: str | None = None
    award_level: str | None = None
    award_date: str | None = None
    description: str | None = None
    evidence_json: dict[str, Any] | None = None


class SkillPayload(ORMModel):
    skill_name: str
    skill_category: str | None = None
    proficiency_level: str | None = None
    source_type: str | None = None
    evidence_json: dict[str, Any] | None = None


class PaperPayload(ORMModel):
    title: str | None = None
    role: str | None = None
    publication_type: str | None = None
    status: str | None = None
    publish_date: str | None = None
    description: str | None = None
    evidence_json: dict[str, Any] | None = None


class PatentPayload(ORMModel):
    patent_name: str | None = None
    patent_type: str | None = None
    role: str | None = None
    status: str | None = None
    application_date: str | None = None
    description: str | None = None
    evidence_json: dict[str, Any] | None = None


class CompetitionPayload(ORMModel):
    competition_name: str | None = None
    award_level: str | None = None
    role: str | None = None
    competition_date: str | None = None
    description: str | None = None
    evidence_json: dict[str, Any] | None = None


class PortraitPayload(ORMModel):
    portrait_mode: str | None = None
    student_type: str | None = None
    capability_tags: list[str] | None = None
    behavior_tags: list[str] | None = None
    job_direction_tags: list[str] | None = None
    research_direction_tags: list[str] | None = None
    method_tags: list[str] | None = None
    academic_potential_tags: list[str] | None = None
    strengths: list[str] | None = None
    risks_or_gaps: list[str] | None = None
    portrait_summary: str | None = None
    confidence_score: float | None = None
    evidence_json: dict[str, Any] | None = None

    @field_validator(
        "capability_tags",
        "behavior_tags",
        "job_direction_tags",
        "research_direction_tags",
        "method_tags",
        "academic_potential_tags",
        "strengths",
        "risks_or_gaps",
        mode="before",
    )
    @classmethod
    def normalize_list_fields(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            return [text]
        return [str(value).strip()] if str(value).strip() else []


class ResumeSectionPayload(ORMModel):
    id: int
    section_type: str
    page_no: int | None = None
    order_no: int
    raw_content: str
    normalized_content: str | None = None


class ExtractLogPayload(ORMModel):
    id: int
    stage_name: str
    model_name: str | None = None
    prompt_version: str | None = None
    input_text: str | None = None
    output_text: str | None = None
    validate_result: dict[str, Any] | None = None
    status: str
    error_message: str | None = None


class ResumeDetailResponse(BaseModel):
    id: int
    source_file_name: str
    analysis_mode: str
    analysis_status: str
    parse_status: str
    extract_status: str
    current_version: int
    raw_text: str | None = None
    sections: list[ResumeSectionPayload]
    basic_info: BasicInfoPayload | None = None
    educations: list[EducationPayload]
    internships: list[InternshipPayload]
    projects: list[ProjectPayload]
    awards: list[AwardPayload]
    papers: list[PaperPayload]
    patents: list[PatentPayload]
    competitions: list[CompetitionPayload]
    skills: list[SkillPayload]
    portrait: PortraitPayload | None = None
    last_error_stage: str | None = None
    last_error_message: str | None = None


class ReviewSaveRequest(BaseModel):
    editor: str = "admin"
    basic_info: BasicInfoPayload | None = None
    educations: list[EducationPayload] = Field(default_factory=list)
    internships: list[InternshipPayload] = Field(default_factory=list)
    projects: list[ProjectPayload] = Field(default_factory=list)
    awards: list[AwardPayload] = Field(default_factory=list)
    papers: list[PaperPayload] = Field(default_factory=list)
    patents: list[PatentPayload] = Field(default_factory=list)
    competitions: list[CompetitionPayload] = Field(default_factory=list)
    skills: list[SkillPayload] = Field(default_factory=list)
    portrait: PortraitPayload | None = None


class DictionaryResponse(BaseModel):
    analysis_modes: list[str]
    degrees: list[str]
    capability_tags: list[str]
    behavior_tags: list[str]
    job_direction_tags: list[str]
    research_direction_tags: list[str]
    method_tags: list[str]
    academic_potential_tags: list[str]
    skill_categories: list[str]


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    analysis_mode: str = "student"
    top_k: int | None = None
    chunk_types: list[str] = Field(default_factory=list)


class SemanticSearchChunkPayload(BaseModel):
    chunk_id: int
    chunk_type: str
    score: float
    distance: float
    rerank_score: float | None = None
    cosine_score: float
    cosine_distance: float
    keyword_score: float | None = None
    rrf_score: float | None = None
    dense_rank: int | None = None
    keyword_rank: int | None = None
    retrieval_sources: list[str] = Field(default_factory=list)
    score_source: str
    content_text: str
    metadata: dict[str, Any] | None = None


class SemanticSearchResultPayload(BaseModel):
    student_id: int | None = None
    resume_id: int
    student_name: str | None = None
    school_name: str | None = None
    major: str | None = None
    analysis_mode: str
    student_type: str | None = None
    best_score: float
    hits: list[SemanticSearchChunkPayload]
