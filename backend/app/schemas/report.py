from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CountItem(BaseModel):
    name: str
    count: int


class CoverageMetric(BaseModel):
    key: str
    label: str
    value: float


class SummaryPayload(BaseModel):
    student_count: int
    raw_resume_count: int
    primary_resume_count: int
    school_count: int
    major_count: int
    avg_project_count: float
    avg_internship_count: float


class BasicDistributionPayload(BaseModel):
    school_levels: list[CountItem] = Field(default_factory=list)
    schools_top: list[CountItem] = Field(default_factory=list)
    majors_top: list[CountItem] = Field(default_factory=list)
    degrees: list[CountItem] = Field(default_factory=list)


class TagDistributionPayload(BaseModel):
    student_types: list[CountItem] = Field(default_factory=list)
    research_direction_tags: list[CountItem] = Field(default_factory=list)
    method_tags: list[CountItem] = Field(default_factory=list)
    academic_potential_tags: list[CountItem] = Field(default_factory=list)
    job_direction_tags: list[CountItem] = Field(default_factory=list)
    capability_tags: list[CountItem] = Field(default_factory=list)
    behavior_tags: list[CountItem] = Field(default_factory=list)


class WordCloudItem(BaseModel):
    name: str
    value: int


class WordCloudPayload(BaseModel):
    research_direction: list[WordCloudItem] = Field(default_factory=list)
    job_direction: list[WordCloudItem] = Field(default_factory=list)


class HeatmapCell(BaseModel):
    x: str
    y: str
    value: int


class HeatmapPayload(BaseModel):
    title: str
    x_labels: list[str] = Field(default_factory=list)
    y_labels: list[str] = Field(default_factory=list)
    cells: list[HeatmapCell] = Field(default_factory=list)


class GroupReportMeta(BaseModel):
    analysis_mode: str
    generated_at: datetime
    raw_resume_count: int
    primary_resume_count: int
    student_count: int


class GroupReportResponse(BaseModel):
    meta: GroupReportMeta
    summary: SummaryPayload
    basic_distribution: BasicDistributionPayload
    coverage: list[CoverageMetric] = Field(default_factory=list)
    tag_distribution: TagDistributionPayload
    wordcloud: WordCloudPayload
    heatmaps: list[HeatmapPayload] = Field(default_factory=list)
