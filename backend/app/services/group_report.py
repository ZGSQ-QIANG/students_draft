from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Resume, ResumeSection, Student, StudentSkill
from app.services.dictionaries import STUDENT_MODE
from app.services.normalizer import Normalizer
from app.schemas.report import (
    BasicDistributionPayload,
    CountItem,
    CoverageMetric,
    GroupReportMeta,
    GroupReportResponse,
    HeatmapCell,
    HeatmapPayload,
    SummaryPayload,
    TagDistributionPayload,
    WordCloudItem,
    WordCloudPayload,
)


class GroupReportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.normalizer = Normalizer()

    def build(self, analysis_mode: str) -> GroupReportResponse:
        analysis_mode = STUDENT_MODE
        primary_resumes = self._load_primary_resumes(analysis_mode)
        raw_resume_count = self._count_raw_resumes(analysis_mode)
        student_ids = {resume.student_id for resume in primary_resumes if resume.student_id is not None}
        student_count = len(student_ids) if student_ids else len(primary_resumes)
        total_students = max(student_count, 1)

        school_levels = Counter()
        schools = Counter()
        majors = Counter()
        degrees = Counter()
        student_types = Counter()
        research_direction_tags = Counter()
        method_tags = Counter()
        academic_potential_tags = Counter()
        job_direction_tags = Counter()
        capability_tags = Counter()
        behavior_tags = Counter()

        project_count = internship_count = paper_count = patent_count = competition_count = award_count = 0
        has_project = has_internship = has_paper = has_patent = has_competition = has_award = has_certificate = 0

        research_skill_map: dict[tuple[str, str], int] = defaultdict(int)
        job_skill_map: dict[tuple[str, str], int] = defaultdict(int)
        skill_counter = Counter()

        for resume in primary_resumes:
            education = resume.educations[0] if resume.educations else None
            portrait = resume.portrait

            if education:
                school_level = self.normalizer._normalize_school_level(education.school_name, education.school_level)
                school_levels[self._safe_label(school_level)] += 1
                schools[self._safe_label(education.school_name)] += 1
                majors[self._safe_label(education.major)] += 1
                degrees[self._safe_label(education.degree)] += 1

            if portrait:
                student_types[self._safe_label(portrait.student_type)] += 1
                research_direction_tags.update(self._normalize_tags(portrait.research_direction_tags))
                method_tags.update(self._normalize_tags(portrait.method_tags))
                academic_potential_tags.update(self._normalize_tags(portrait.academic_potential_tags))
                job_direction_tags.update(self._normalize_tags(portrait.job_direction_tags))
                capability_tags.update(self._normalize_tags(portrait.capability_tags))
                behavior_tags.update(self._normalize_tags(portrait.behavior_tags))

            project_count += len(resume.projects)
            internship_count += len(resume.internships)
            paper_count += len(resume.papers)
            patent_count += len(resume.patents)
            competition_count += len(resume.competitions)
            award_count += len(resume.awards)
            has_project += int(bool(resume.projects))
            has_internship += int(bool(resume.internships))
            has_paper += int(bool(resume.papers))
            has_patent += int(bool(resume.patents))
            has_competition += int(bool(resume.competitions))
            has_award += int(bool(resume.awards))
            has_certificate += int(any(section.section_type == "certificate" for section in resume.sections))

            research_tags = self._normalize_tags(portrait.research_direction_tags) if portrait else []
            job_tags = self._normalize_tags(portrait.job_direction_tags) if portrait else []
            skill_names = self._normalize_skill_names(resume.skills)
            for skill in skill_names:
                skill_counter[skill] += 1
            for direction in research_tags:
                for skill in skill_names:
                    research_skill_map[(direction, skill)] += 1
            for direction in job_tags:
                for skill in skill_names:
                    job_skill_map[(direction, skill)] += 1

        top_skills = [name for name, _ in skill_counter.most_common(12)]
        top_research_directions = [name for name, _ in research_direction_tags.most_common(10)]
        top_job_directions = [name for name, _ in job_direction_tags.most_common(10)]

        return GroupReportResponse(
            meta=GroupReportMeta(
                analysis_mode=analysis_mode,
                generated_at=datetime.now(),
                raw_resume_count=raw_resume_count,
                primary_resume_count=len(primary_resumes),
                student_count=student_count,
            ),
            summary=SummaryPayload(
                student_count=student_count,
                raw_resume_count=raw_resume_count,
                primary_resume_count=len(primary_resumes),
                school_count=len([key for key in schools if key != "未知"]),
                major_count=len([key for key in majors if key != "未知"]),
                avg_project_count=round(project_count / total_students, 2),
                avg_internship_count=round(internship_count / total_students, 2),
            ),
            basic_distribution=BasicDistributionPayload(
                school_levels=self._to_count_items(school_levels),
                schools_top=self._to_count_items(schools, limit=10),
                majors_top=self._to_count_items(majors, limit=10),
                degrees=self._to_count_items(degrees),
            ),
            coverage=[
                CoverageMetric(key="project", label="项目经历覆盖率", value=round(has_project / total_students, 4)),
                CoverageMetric(key="internship", label="实习经历覆盖率", value=round(has_internship / total_students, 4)),
                CoverageMetric(key="paper", label="论文覆盖率", value=round(has_paper / total_students, 4)),
                CoverageMetric(key="patent", label="专利覆盖率", value=round(has_patent / total_students, 4)),
                CoverageMetric(key="competition", label="竞赛覆盖率", value=round(has_competition / total_students, 4)),
                CoverageMetric(key="award", label="奖项覆盖率", value=round(has_award / total_students, 4)),
                CoverageMetric(key="certificate", label="证书覆盖率", value=round(has_certificate / total_students, 4)),
            ],
            tag_distribution=TagDistributionPayload(
                student_types=self._to_count_items(student_types),
                research_direction_tags=self._to_count_items(research_direction_tags, limit=10),
                method_tags=self._to_count_items(method_tags, limit=10),
                academic_potential_tags=self._to_count_items(academic_potential_tags, limit=10),
                job_direction_tags=self._to_count_items(job_direction_tags, limit=10),
                capability_tags=self._to_count_items(capability_tags, limit=10),
                behavior_tags=self._to_count_items(behavior_tags, limit=10),
            ),
            wordcloud=WordCloudPayload(
                research_direction=[WordCloudItem(name=name, value=count) for name, count in research_direction_tags.most_common(30)],
                job_direction=[WordCloudItem(name=name, value=count) for name, count in job_direction_tags.most_common(30)],
            ),
            heatmaps=[
                HeatmapPayload(
                    title="研究方向 × 技能热力图",
                    x_labels=top_skills,
                    y_labels=top_research_directions,
                    cells=self._build_heatmap_cells(research_skill_map, top_research_directions, top_skills),
                ),
                HeatmapPayload(
                    title="岗位方向 × 技能热力图",
                    x_labels=top_skills,
                    y_labels=top_job_directions,
                    cells=self._build_heatmap_cells(job_skill_map, top_job_directions, top_skills),
                ),
            ],
        )

    def _load_primary_resumes(self, analysis_mode: str) -> list[Resume]:
        query = (
            select(Resume)
            .where(Resume.analysis_mode == analysis_mode, Resume.is_primary.is_(True))
            .options(
                selectinload(Resume.student),
                selectinload(Resume.basic_info),
                selectinload(Resume.educations),
                selectinload(Resume.projects),
                selectinload(Resume.internships),
                selectinload(Resume.papers),
                selectinload(Resume.patents),
                selectinload(Resume.competitions),
                selectinload(Resume.awards),
                selectinload(Resume.skills),
                selectinload(Resume.portrait),
                selectinload(Resume.sections),
            )
            .order_by(Resume.created_at.desc(), Resume.id.desc())
        )
        return list(self.db.execute(query).scalars().all())

    def _count_raw_resumes(self, analysis_mode: str) -> int:
        return int(
            self.db.execute(select(func.count(Resume.id)).where(Resume.analysis_mode == analysis_mode)).scalar_one() or 0
        )

    @staticmethod
    def _normalize_tags(values: list[str] | None) -> list[str]:
        return [value.strip() for value in (values or []) if value and value.strip()]

    @staticmethod
    def _normalize_skill_names(skills: list[StudentSkill]) -> list[str]:
        names = []
        for skill in skills:
            if skill.skill_name and skill.skill_name.strip():
                names.append(skill.skill_name.strip())
        return names

    @staticmethod
    def _safe_label(value: str | None) -> str:
        return value.strip() if value and value.strip() else "未知"

    @staticmethod
    def _to_count_items(counter: Counter[str], limit: int | None = None) -> list[CountItem]:
        items = counter.most_common(limit)
        return [CountItem(name=name, count=count) for name, count in items]

    @staticmethod
    def _build_heatmap_cells(
        source: dict[tuple[str, str], int],
        directions: list[str],
        skills: list[str],
    ) -> list[HeatmapCell]:
        return [
            HeatmapCell(x=skill, y=direction, value=source.get((direction, skill), 0))
            for direction in directions
            for skill in skills
        ]
