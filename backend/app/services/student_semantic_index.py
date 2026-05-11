from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Resume
from app.services.audit import create_log
from app.services.semantic_chunking import ChunkBuilder
from app.services.student_vector_store import StudentVectorStore


class StudentSemanticIndexService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.chunk_builder = ChunkBuilder()
        self.vector_store = StudentVectorStore()

    def reindex_resume(self, resume_id: int) -> dict[str, object]:
        resume = self._load_resume(resume_id)
        if resume is None:
            return {"success": False, "chunk_count": 0, "error": "resume_not_found"}

        chunks = self.chunk_builder.build(resume)
        try:
            indexed_rows = self.vector_store.reindex_resume(self.db, resume, chunks)
            create_log(
                self.db,
                resume_id,
                "build_semantic_index",
                output={"chunk_count": len(indexed_rows), "analysis_mode": resume.analysis_mode},
                validate_result={"indexed": len(indexed_rows)},
            )
            self.db.commit()
            return {"success": True, "chunk_count": len(indexed_rows)}
        except Exception as exc:
            create_log(
                self.db,
                resume_id,
                "build_semantic_index",
                status="failed",
                error_message=str(exc),
                output={"chunk_count": len(chunks), "analysis_mode": resume.analysis_mode},
            )
            self.db.commit()
            return {"success": False, "chunk_count": len(chunks), "error": str(exc)}

    def _load_resume(self, resume_id: int) -> Resume | None:
        query = (
            select(Resume)
            .where(Resume.id == resume_id)
            .options(
                selectinload(Resume.sections),
                selectinload(Resume.basic_info),
                selectinload(Resume.educations),
                selectinload(Resume.internships),
                selectinload(Resume.projects),
                selectinload(Resume.awards),
                selectinload(Resume.papers),
                selectinload(Resume.patents),
                selectinload(Resume.competitions),
                selectinload(Resume.skills),
                selectinload(Resume.portrait),
                selectinload(Resume.resume_chunks),
            )
        )
        return self.db.execute(query).scalar_one_or_none()
