from __future__ import annotations

import traceback
from typing import Any

from sqlalchemy.orm import Session

from app.models import Resume
from app.services.audit import create_log
from app.services.llm_extractor import LLMExtractor
from app.services.normalizer import Normalizer
from app.services.parser import DocumentParser
from app.services.portrait import PortraitEngine
from app.services.repository import ResumeRepository
from app.services.rule_extractor import RuleExtractor
from app.services.segmenter import SectionSegmenter
from app.services.vectorize import Vectorizer


class ResumePipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ResumeRepository(db)
        self.parser = DocumentParser()
        self.segmenter = SectionSegmenter()
        self.rule_extractor = RuleExtractor()
        self.llm_extractor = LLMExtractor()
        self.normalizer = Normalizer()
        self.portrait_engine = PortraitEngine()
        self.vectorizer = Vectorizer()

    def run(self, resume_id: int) -> None:
        resume = self.db.get(Resume, resume_id)
        if not resume:
            return
        try:
            self._parse(resume)
            sections = self._segment(resume)
            extracted = self._extract(resume, sections)
            normalized = self.normalizer.normalize(extracted)
            portrait = self.llm_extractor.generate_portrait(normalized, sections)
            normalized["portrait"] = {**portrait, **self.portrait_engine.build({**normalized, "portrait": portrait})}
            self.repository.replace_structured_data(resume, normalized)
            self.repository.replace_embeddings(resume, self._build_embeddings(resume, normalized))
            resume.extract_status = "completed"
            resume.parse_status = "completed"
            resume.last_error_stage = None
            resume.last_error_message = None
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            failed_resume = self.db.get(Resume, resume_id)
            if failed_resume:
                failed_resume.parse_status = "failed"
                failed_resume.extract_status = "failed"
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

    def _build_embeddings(self, resume: Resume, payload: dict[str, Any]) -> list[dict[str, Any]]:
        items = []
        if resume.raw_text:
            items.append(
                {
                    "resume_id": resume.id,
                    "section_id": None,
                    "doc_type": "resume_full",
                    "text": resume.raw_text,
                    "metadata_json": {"file_name": resume.source_file_name},
                    "embedding": self.vectorizer.embed(resume.raw_text),
                }
            )
        for section in resume.sections:
            if section.section_type in {"project", "internship"}:
                items.append(
                    {
                        "resume_id": resume.id,
                        "section_id": section.id,
                        "doc_type": section.section_type,
                        "text": section.raw_content,
                        "metadata_json": {"section_type": section.section_type},
                        "embedding": self.vectorizer.embed(section.raw_content),
                    }
                )
        portrait_summary = payload.get("portrait", {}).get("portrait_summary")
        if portrait_summary:
            items.append(
                {
                    "resume_id": resume.id,
                    "section_id": None,
                    "doc_type": "portrait",
                    "text": portrait_summary,
                    "metadata_json": {"student_type": payload.get("portrait", {}).get("student_type")},
                    "embedding": self.vectorizer.embed(portrait_summary),
                }
            )
        return items

