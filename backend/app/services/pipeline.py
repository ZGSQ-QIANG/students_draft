from __future__ import annotations

import traceback
from typing import Any

from sqlalchemy.orm import Session

from app.models import Resume
from app.services.audit import create_log
from app.services.dictionaries import STUDENT_MODE
from app.services.llm_extractor import LLMExtractor
from app.services.normalizer import Normalizer
from app.services.parser import DocumentParser
from app.services.portrait import build_portrait_engine
from app.services.repository import ResumeRepository
from app.services.rule_extractor import RuleExtractor
from app.services.segmenter import SectionSegmenter
from app.services.student_semantic_index import StudentSemanticIndexService
from app.services.student_identity import StudentIdentityService


class ResumePipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ResumeRepository(db)
        self.parser = DocumentParser()
        self.segmenter = SectionSegmenter()
        self.rule_extractor = RuleExtractor()
        self.llm_extractor = LLMExtractor()
        self.normalizer = Normalizer()
        self.semantic_index = StudentSemanticIndexService(db)
        self.identity_service = StudentIdentityService(db)

    def run(self, resume_id: int) -> None:
        resume = self.db.get(Resume, resume_id)
        if not resume:
            return
        try:
            resume.analysis_status = "parsing"
            self._parse(resume)
            sections = self._segment(resume)
            extracted = self._extract(resume, sections)
            normalized = self.normalizer.normalize(extracted)
            resume.analysis_mode = STUDENT_MODE
            portrait = self.llm_extractor.generate_portrait(normalized, sections)
            portrait_engine = build_portrait_engine()
            normalized["portrait"] = {**portrait, **portrait_engine.build({**normalized, "portrait": portrait})}
            self.repository.replace_structured_data(resume, normalized)
            self.db.flush()
            self.identity_service.resolve_resume(resume)
            resume.extract_status = "completed"
            resume.parse_status = "completed"
            resume.analysis_status = "completed"
            resume.last_error_stage = None
            resume.last_error_message = None
            self.db.commit()
            self.semantic_index.reindex_resume(resume.id)
        except Exception as exc:
            self.db.rollback()
            failed_resume = self.db.get(Resume, resume_id)
            if failed_resume:
                failed_resume.parse_status = "failed"
                failed_resume.extract_status = "failed"
                failed_resume.analysis_status = "failed"
                failed_resume.last_error_stage = failed_resume.last_error_stage or "pipeline"
                failed_resume.last_error_message = str(exc)
                create_log(
                    self.db,
                    resume_id,
                    stage_name=failed_resume.last_error_stage,
                    status="failed",
                    error_message="".join(traceback.format_exception_only(type(exc), exc)).strip(),
                )
                self.db.commit()

    def _parse(self, resume: Resume) -> None:
        resume.parse_status = "parsing"
        self.db.flush()
        parsed = self.parser.parse(resume.source_file_path)
        resume.raw_text = parsed.raw_text
        resume.ocr_text = parsed.ocr_text
        resume.page_texts = parsed.page_texts
        resume.parse_status = "parsed"
        create_log(self.db, resume.id, "parse_resume", output={"pages": len(parsed.page_texts)})

    def _segment(self, resume: Resume) -> dict[str, list[str]]:
        sections = self.segmenter.segment(resume.raw_text or "")
        section_rows = []
        order_no = 0
        for section_type, items in sections.items():
            for item in items:
                section_rows.append(
                    {
                        "resume_id": resume.id,
                        "section_type": section_type,
                        "page_no": 1,
                        "order_no": order_no,
                        "raw_content": item,
                        "normalized_content": item,
                    }
                )
                order_no += 1
        self.repository.replace_sections(resume, section_rows)
        resume.section_snapshot = sections
        create_log(self.db, resume.id, "segment_resume", output=sections, validate_result={"section_count": order_no})
        return sections

    def _extract(self, resume: Resume, sections: dict[str, list[str]]) -> dict[str, Any]:
        resume.extract_status = "extracting"
        resume.analysis_status = "extracting"
        rule_payload = self.rule_extractor.extract(sections)
        create_log(self.db, resume.id, "rule_extract", output=rule_payload)
        internships = self.llm_extractor.enrich_experiences("internship", sections.get("internship", []), rule_payload["internships"])
        projects = self.llm_extractor.enrich_experiences("project", sections.get("project", []), rule_payload["projects"])
        combined = {**rule_payload, "internships": internships, "projects": projects, "portrait": {}}
        create_log(
            self.db,
            resume.id,
            "llm_extract",
            model_name=self.llm_extractor.provider.model_name,
            prompt_version="v1",
            output=combined,
        )
        resume.extract_status = "extracted"
        return combined
