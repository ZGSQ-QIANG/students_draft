from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Resume, StudentResumeChunk
from app.services.dictionaries import STUDENT_MODE

try:
    import jieba
    from langchain_community.retrievers import BM25Retriever
    from langchain_core.documents import Document
except ImportError:  # pragma: no cover - runtime dependency is validated when searching.
    jieba = None  # type: ignore[assignment]
    BM25Retriever = None  # type: ignore[assignment]
    Document = Any  # type: ignore[misc, assignment]


class StudentBM25Retriever:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(
        self,
        query: str,
        analysis_mode: str,
        *,
        top_k: int,
        chunk_types: list[str] | None = None,
    ) -> list[Document]:
        if BM25Retriever is None or jieba is None:
            raise RuntimeError("langchain-community, rank-bm25 and jieba are required for BM25 retrieval.")

        documents = self._load_documents(STUDENT_MODE, chunk_types or [])
        if not documents:
            return []

        retriever = BM25Retriever.from_documents(
            documents,
            preprocess_func=tokenize_for_bm25,
            k=top_k,
        )
        return list(retriever.invoke(query))

    def _load_documents(self, analysis_mode: str, chunk_types: list[str]) -> list[Document]:
        query = select(StudentResumeChunk).where(
            StudentResumeChunk.analysis_mode == STUDENT_MODE,
            StudentResumeChunk.index_status == "indexed",
        ).join(Resume, Resume.id == StudentResumeChunk.resume_id).where(Resume.is_primary.is_(True))
        if chunk_types:
            query = query.where(StudentResumeChunk.chunk_type.in_(chunk_types))
        rows = self.db.execute(query.order_by(StudentResumeChunk.id)).scalars().all()
        return [
            Document(
                page_content=row.content_text,
                metadata={
                    "chunk_id": row.id,
                    "resume_id": row.resume_id,
                    "analysis_mode": row.analysis_mode,
                    "chunk_type": row.chunk_type,
                },
            )
            for row in rows
        ]


def tokenize_for_bm25(text: str) -> list[str]:
    if jieba is None:
        return []
    normalized = text.lower()
    tokens = [token.strip() for token in jieba.lcut(normalized) if token.strip()]
    ascii_terms = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]*|\d+(?:\.\d+)?", normalized)
    return [token for token in tokens + ascii_terms if token]
