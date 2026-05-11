from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import StudentResumeChunk
from app.services.dictionaries import STUDENT_MODE
from app.services.embedding_provider import EmbeddingsProvider
from app.services.keyword_retriever import StudentBM25Retriever
from app.services.rerank_provider import build_rerank_compressor
from app.services.student_vector_store import StudentVectorStore

try:
    from langchain_core.documents import Document
except ImportError:  # pragma: no cover - runtime dependency is validated when searching.
    Document = Any  # type: ignore[misc, assignment]


class StudentRetrieverService:
    def __init__(self, db: Session, embeddings_provider: EmbeddingsProvider | None = None) -> None:
        self.db = db
        self.settings = get_settings()
        self.embeddings_provider = embeddings_provider
        self.vector_store = StudentVectorStore(embeddings_provider)
        self.keyword_retriever = StudentBM25Retriever(db)

    def search(
        self,
        query: str,
        analysis_mode: str,
        *,
        top_k: int | None = None,
        chunk_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        analysis_mode = STUDENT_MODE
        store = self.vector_store._build_store(analysis_mode)
        requested_top_k = top_k or self.settings.semantic_search_top_k
        fetch_k = max(requested_top_k * self.settings.dense_top_k_multiplier, requested_top_k + 5)
        vector_filter = {"chunk_type": chunk_types[0]} if chunk_types and len(chunk_types) == 1 else None
        search_kwargs: dict[str, Any] = {"k": fetch_k}
        if vector_filter:
            search_kwargs["filter"] = vector_filter
        docs_with_scores = store.similarity_search_with_score(query, **search_kwargs)

        allowed_chunk_types = set(chunk_types or [])
        dense_hits: list[dict[str, Any]] = []
        for document, distance in docs_with_scores:
            metadata = getattr(document, "metadata", {}) or {}
            chunk_type = metadata.get("chunk_type")
            if allowed_chunk_types and chunk_type not in allowed_chunk_types:
                continue
            chunk_id = metadata.get("chunk_id")
            if chunk_id is None:
                continue
            chunk_id = int(chunk_id)
            dense_hits.append({"chunk_id": chunk_id, "distance": float(distance), "document": document})

        keyword_hits = self._keyword_search(query, analysis_mode, requested_top_k, chunk_types or [])
        fused_hits = self._rrf_fuse(dense_hits, keyword_hits)

        if not fused_hits:
            return []
        if self.settings.rerank_enabled and self.settings.rerank_max_candidates > 0:
            fused_hits = fused_hits[: self.settings.rerank_max_candidates]
        chunk_ids = [hit["chunk_id"] for hit in fused_hits]

        chunk_rows = self.db.execute(
            select(StudentResumeChunk).where(StudentResumeChunk.id.in_(chunk_ids), StudentResumeChunk.index_status == "indexed")
        ).scalars()
        row_map = {row.id: row for row in chunk_rows}
        chunk_hits = self._build_chunk_hits_from_rrf(fused_hits, row_map)
        chunk_hits = self._rerank_or_fallback(query, chunk_hits, row_map, requested_top_k)
        return self._group_chunk_hits(chunk_hits, row_map, analysis_mode, requested_top_k)

    @staticmethod
    def _group_chunk_hits(
        chunk_hits: list[dict[str, Any]],
        row_map: dict[int, StudentResumeChunk],
        analysis_mode: str,
        requested_top_k: int,
    ) -> list[dict[str, Any]]:
        grouped: dict[int, dict[str, Any]] = defaultdict(dict)

        for hit in chunk_hits:
            row = row_map.get(hit["chunk_id"])
            if row is None:
                continue
            metadata = row.metadata_json or {}
            resume_id = row.resume_id
            student_id = metadata.get("student_id")
            group_id = int(student_id) if student_id is not None else resume_id
            item = grouped.get(group_id)
            if not item:
                item = {
                    "student_id": student_id,
                    "resume_id": resume_id,
                    "student_name": metadata.get("student_name"),
                    "school_name": metadata.get("school_name"),
                    "major": metadata.get("major"),
                    "analysis_mode": metadata.get("analysis_mode", analysis_mode),
                    "student_type": metadata.get("student_type"),
                    "best_score": hit["score"],
                    "hits": [],
                }
                grouped[group_id] = item
            else:
                item["best_score"] = max(item["best_score"], hit["score"])

            item["hits"].append(
                {
                    "chunk_id": row.id,
                    "chunk_type": row.chunk_type,
                    "score": hit["score"],
                    "distance": hit.get("distance", 0.0),
                    "rerank_score": hit.get("rerank_score"),
                    "cosine_score": hit.get("cosine_score", hit["score"]),
                    "cosine_distance": hit.get("cosine_distance", hit.get("distance", 0.0)),
                    "keyword_score": hit.get("keyword_score"),
                    "rrf_score": hit.get("rrf_score"),
                    "dense_rank": hit.get("dense_rank"),
                    "keyword_rank": hit.get("keyword_rank"),
                    "retrieval_sources": hit.get("retrieval_sources", []),
                    "score_source": hit.get("score_source", "cosine"),
                    "content_text": row.content_text,
                    "metadata": metadata,
                }
            )

        results = sorted(grouped.values(), key=lambda item: item["best_score"], reverse=True)
        for item in results:
            item["hits"] = sorted(item["hits"], key=lambda hit: hit["score"], reverse=True)[:requested_top_k]
        return results[:requested_top_k]

    def _keyword_search(
        self,
        query: str,
        analysis_mode: str,
        requested_top_k: int,
        chunk_types: list[str],
    ) -> list[dict[str, Any]]:
        if not self.settings.hybrid_search_enabled:
            return []
        try:
            documents = self.keyword_retriever.search(
                query,
                analysis_mode,
                top_k=max(self.settings.bm25_top_k, requested_top_k),
                chunk_types=chunk_types,
            )
        except Exception:
            return []

        hits: list[dict[str, Any]] = []
        for rank, document in enumerate(documents, start=1):
            metadata = getattr(document, "metadata", {}) or {}
            chunk_id = metadata.get("chunk_id")
            if chunk_id is None:
                continue
            hits.append({"chunk_id": int(chunk_id), "keyword_rank": rank, "document": document})
        return hits

    def _rrf_fuse(self, dense_hits: list[dict[str, Any]], keyword_hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        fused: dict[int, dict[str, Any]] = {}

        for rank, hit in enumerate(dense_hits, start=1):
            chunk_id = hit["chunk_id"]
            item = fused.setdefault(chunk_id, {"chunk_id": chunk_id, "retrieval_sources": []})
            item["dense_rank"] = rank
            item["cosine_distance"] = hit["distance"]
            item["cosine_score"] = max(0.0, 1.0 - hit["distance"])
            item["dense_rrf_score"] = self.settings.rrf_dense_weight / (self.settings.rrf_k + rank)
            item["retrieval_sources"].append("dense")

        for hit in keyword_hits:
            rank = hit["keyword_rank"]
            chunk_id = hit["chunk_id"]
            item = fused.setdefault(chunk_id, {"chunk_id": chunk_id, "retrieval_sources": []})
            item["keyword_rank"] = rank
            item["keyword_score"] = 1.0 / rank
            item["keyword_rrf_score"] = self.settings.rrf_keyword_weight / (self.settings.rrf_k + rank)
            item["retrieval_sources"].append("keyword")

        for item in fused.values():
            item["retrieval_sources"] = sorted(set(item["retrieval_sources"]))
            item["cosine_score"] = item.get("cosine_score", 0.0)
            item["cosine_distance"] = item.get("cosine_distance", 1.0)
            item["keyword_score"] = item.get("keyword_score")
            item["rrf_score"] = item.get("dense_rrf_score", 0.0) + item.get("keyword_rrf_score", 0.0)

        return sorted(fused.values(), key=lambda item: item["rrf_score"], reverse=True)

    @staticmethod
    def _build_chunk_hits_from_rrf(
        fused_hits: list[dict[str, Any]],
        row_map: dict[int, StudentResumeChunk],
    ) -> list[dict[str, Any]]:
        chunk_hits: list[dict[str, Any]] = []
        for hit in fused_hits:
            chunk_id = hit["chunk_id"]
            row = row_map.get(chunk_id)
            if row is None:
                continue
            rrf_score = hit.get("rrf_score", 0.0)
            chunk_hits.append(
                {
                    "chunk_id": chunk_id,
                    "score": rrf_score,
                    "distance": 1.0 - rrf_score,
                    "rerank_score": None,
                    "cosine_score": hit.get("cosine_score", 0.0),
                    "cosine_distance": hit.get("cosine_distance", 1.0),
                    "keyword_score": hit.get("keyword_score"),
                    "rrf_score": rrf_score,
                    "dense_rank": hit.get("dense_rank"),
                    "keyword_rank": hit.get("keyword_rank"),
                    "retrieval_sources": hit.get("retrieval_sources", []),
                    "score_source": "rrf",
                    "content_text": row.content_text,
                    "chunk_type": row.chunk_type,
                }
            )
        return sorted(chunk_hits, key=lambda hit: hit["score"], reverse=True)

    def _rerank_or_fallback(
        self,
        query: str,
        chunk_hits: list[dict[str, Any]],
        row_map: dict[int, StudentResumeChunk],
        requested_top_k: int,
    ) -> list[dict[str, Any]]:
        if not self.settings.rerank_enabled or not chunk_hits:
            return chunk_hits

        documents = []
        for hit in chunk_hits:
            row = row_map.get(hit["chunk_id"])
            if row is None:
                continue
            documents.append(Document(page_content=row.content_text, metadata={**hit}))

        try:
            compressor = build_rerank_compressor(self.settings, top_n=max(requested_top_k * 3, requested_top_k))
            reranked_documents = compressor.compress_documents(documents, query)
        except Exception:
            return [
                {
                    **hit,
                    "score": hit.get("rrf_score", hit["score"]),
                    "distance": 1.0 - hit.get("rrf_score", hit["score"]),
                    "rerank_score": None,
                    "score_source": "rrf_fallback",
                }
                for hit in chunk_hits
            ]

        reranked_hits = []
        for document in reranked_documents:
            metadata = dict(document.metadata or {})
            rerank_score = float(metadata.get("rerank_score", 0.0))
            reranked_hits.append(
                {
                    **metadata,
                    "score": rerank_score,
                    "distance": 1.0 - rerank_score,
                    "rerank_score": rerank_score,
                    "cosine_score": float(metadata.get("cosine_score", 0.0)),
                    "cosine_distance": float(metadata.get("cosine_distance", 0.0)),
                    "keyword_score": metadata.get("keyword_score"),
                    "rrf_score": float(metadata.get("rrf_score", 0.0)),
                    "dense_rank": metadata.get("dense_rank"),
                    "keyword_rank": metadata.get("keyword_rank"),
                    "retrieval_sources": metadata.get("retrieval_sources", []),
                    "score_source": "rerank",
                }
            )
        return sorted(reranked_hits, key=lambda hit: hit["score"], reverse=True)
