from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Resume, StudentResumeChunk
from app.services.dictionaries import STUDENT_MODE
from app.services.embedding_provider import EmbeddingsProvider, build_embeddings_provider
from app.services.semantic_chunking import ChunkPayload


class StudentVectorStore:
    _store_cache: dict[str, Any] = {}

    def __init__(self, embeddings_provider: EmbeddingsProvider | None = None) -> None:
        self.settings = get_settings()
        self.embeddings_provider = embeddings_provider

    def reindex_resume(self, db: Session, resume: Resume, chunks: list[ChunkPayload]) -> list[StudentResumeChunk]:
        existing_rows = list(resume.resume_chunks)
        for row in existing_rows:
            db.delete(row)
        db.flush()

        store = self._build_store(STUDENT_MODE)
        self._delete_resume_docs(store, resume.id)
        self._clear_superseded_resume_indexes(db, store, resume)

        if not resume.is_primary:
            return []

        chunk_rows = [
            StudentResumeChunk(
                resume_id=resume.id,
                analysis_mode=STUDENT_MODE,
                chunk_type=payload.chunk_type,
                source_table=payload.source_table,
                source_row_id=payload.source_row_id,
                chunk_order=payload.chunk_order,
                content_text=payload.content_text,
                metadata_json=payload.metadata_json,
                index_status="pending",
            )
            for payload in chunks
        ]
        db.add_all(chunk_rows)
        db.flush()
        if not chunk_rows:
            return []

        documents = [self._to_document(row) for row in chunk_rows]
        ids = [self._document_id(row.id) for row in chunk_rows]
        try:
            store.add_documents(documents=documents, ids=ids)
        except Exception:
            for row in chunk_rows:
                row.index_status = "failed"
            raise

        for row in chunk_rows:
            row.index_status = "indexed"
        return chunk_rows

    def _clear_superseded_resume_indexes(self, db: Session, store: Any, resume: Resume) -> None:
        if resume.student_id is None:
            return
        related_resumes = db.execute(
            select(Resume).where(Resume.student_id == resume.student_id, Resume.id != resume.id, Resume.is_primary.is_(False))
        ).scalars()
        for item in related_resumes:
            self._delete_resume_docs(store, item.id)
            for row in item.resume_chunks:
                row.index_status = "superseded"

    def _build_store(self, analysis_mode: str):
        analysis_mode = STUDENT_MODE
        cached = StudentVectorStore._store_cache.get(analysis_mode)
        if cached is not None:
            return cached

        try:
            from langchain_chroma import Chroma
        except ImportError as exc:
            raise RuntimeError("langchain_chroma is required for semantic indexing.") from exc

        try:
            if self.embeddings_provider is None:
                self.embeddings_provider = build_embeddings_provider(self.settings)
            embedding_function = self.embeddings_provider
        except Exception as exc:
            raise RuntimeError(str(exc)) from exc

        store = Chroma(
            collection_name=self._collection_name(analysis_mode),
            persist_directory=str(self.settings.chroma_path),
            embedding_function=embedding_function,
        )
        StudentVectorStore._store_cache[analysis_mode] = store
        return store

    def _delete_resume_docs(self, store: Any, resume_id: int) -> None:
        try:
            store.delete(where={"resume_id": resume_id})
        except Exception:
            return

    @staticmethod
    def _document_id(chunk_id: int) -> str:
        return f"resume-chunk-{chunk_id}"

    def _to_document(self, row: StudentResumeChunk):
        try:
            from langchain_core.documents import Document
        except ImportError as exc:
            raise RuntimeError("langchain_core is required for semantic indexing.") from exc

        return Document(page_content=row.content_text, metadata=self._store_metadata(row))

    @staticmethod
    def _store_metadata(row: StudentResumeChunk) -> dict[str, Any]:
        source = row.metadata_json or {}
        metadata: dict[str, Any] = {
            "chunk_id": row.id,
            "resume_id": row.resume_id,
            "analysis_mode": row.analysis_mode,
            "chunk_type": row.chunk_type,
            "source_table": row.source_table,
            "source_row_id": row.source_row_id or 0,
        }
        for key, value in source.items():
            if value is None:
                continue
            if isinstance(value, list):
                metadata[key] = " | ".join(str(item) for item in value if item is not None)
            elif isinstance(value, (str, int, float, bool)):
                metadata[key] = value
        return metadata

    @staticmethod
    def _collection_name(analysis_mode: str) -> str:
        return f"student_resume_chunks_{STUDENT_MODE}"
