from __future__ import annotations

from threading import Lock
from typing import Any, Sequence

from pydantic import ConfigDict

from app.core.config import Settings, get_settings

try:
    from langchain_core.documents import Document
    from langchain_core.documents.compressor import BaseDocumentCompressor
except ImportError:  # pragma: no cover - runtime dependency is validated when searching.
    Document = Any  # type: ignore[misc, assignment]

    class BaseDocumentCompressor:  # type: ignore[no-redef]
        pass


_RERANKER_CACHE: dict[tuple[str, str, int, int], Qwen3LocalReranker] = {}
_RERANKER_CACHE_LOCK = Lock()


class Qwen3LocalReranker:
    def __init__(self, settings: Settings) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("transformers and torch are required for local Qwen3 reranking.") from exc

        if not settings.rerank_model_path.strip():
            raise ValueError("RERANK_MODEL_PATH is required when using qwen3_local reranker.")

        self.torch = torch
        self.model_path = settings.rerank_model_path
        self.device = _resolve_torch_device(settings.rerank_device, torch)
        self.batch_size = settings.rerank_batch_size
        self.max_length = settings.rerank_max_length
        self.instruction = settings.rerank_instruction.strip()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, padding_side="left")
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path, torch_dtype="auto").eval()
        self.model.to(self.device)
        self.token_false_id = self._token_id("no")
        self.token_true_id = self._token_id("yes")
        self.prefix = (
            "<|im_start|>system\n"
            'Judge whether the Document meets the requirements based on the Query and the Instruct provided. '
            'Note that the answer can only be "yes" or "no".'
            "<|im_end|>\n<|im_start|>user\n"
        )
        self.suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        self.prefix_tokens = self.tokenizer.encode(self.prefix, add_special_tokens=False)
        self.suffix_tokens = self.tokenizer.encode(self.suffix, add_special_tokens=False)

    def score_documents(self, query: str, documents: Sequence[str]) -> list[float]:
        if not documents:
            return []

        scores: list[float] = []
        pairs = [self._format_instruction(query, document) for document in documents]
        for start in range(0, len(pairs), self.batch_size):
            batch = pairs[start : start + self.batch_size]
            inputs = self._process_inputs(batch)
            scores.extend(self._compute_logits(inputs))
        return scores

    def _format_instruction(self, query: str, document: str) -> str:
        instruction = self.instruction or "Given a web search query, retrieve relevant passages that answer the query"
        return f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {document}"

    def _process_inputs(self, pairs: Sequence[str]) -> dict[str, Any]:
        body_max_length = max(self.max_length - len(self.prefix_tokens) - len(self.suffix_tokens), 1)
        inputs = self.tokenizer(
            list(pairs),
            padding=False,
            truncation="longest_first",
            return_attention_mask=False,
            max_length=body_max_length,
        )
        for index, input_ids in enumerate(inputs["input_ids"]):
            inputs["input_ids"][index] = self.prefix_tokens + input_ids + self.suffix_tokens
        padded = self.tokenizer.pad(inputs, padding=True, return_tensors="pt")
        return {key: value.to(self.model.device) for key, value in padded.items()}

    def _compute_logits(self, inputs: dict[str, Any]) -> list[float]:
        with self.torch.no_grad():
            batch_scores = self.model(**inputs).logits[:, -1, :]
            true_vector = batch_scores[:, self.token_true_id]
            false_vector = batch_scores[:, self.token_false_id]
            batch_scores = self.torch.stack([false_vector, true_vector], dim=1)
            batch_scores = self.torch.nn.functional.log_softmax(batch_scores, dim=1)
            return batch_scores[:, 1].exp().detach().cpu().tolist()

    def _token_id(self, token: str) -> int:
        token_id = self.tokenizer.convert_tokens_to_ids(token)
        if token_id is None or token_id == self.tokenizer.unk_token_id:
            token_ids = self.tokenizer(token, add_special_tokens=False).input_ids
            if not token_ids:
                raise ValueError(f"Cannot resolve token id for {token!r}.")
            return int(token_ids[-1])
        return int(token_id)


def _resolve_torch_device(device: str, torch_module) -> str:
    requested = (device or "cpu").strip().lower()
    if requested == "mps" and not torch_module.backends.mps.is_available():
        return "cpu"
    if requested == "cuda" and not torch_module.cuda.is_available():
        return "cpu"
    return requested or "cpu"


class Qwen3RerankCompressor(BaseDocumentCompressor):
    reranker: Any
    top_n: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Any | None = None,
    ) -> Sequence[Document]:
        scores = self.reranker.score_documents(query, [document.page_content for document in documents])
        reranked: list[Document] = []
        for document, score in zip(documents, scores):
            metadata = dict(document.metadata or {})
            metadata["rerank_score"] = float(score)
            metadata["score"] = float(score)
            metadata["score_source"] = "rerank"
            reranked.append(Document(page_content=document.page_content, metadata=metadata))
        reranked.sort(key=lambda document: document.metadata.get("rerank_score", 0.0), reverse=True)
        return reranked[: self.top_n] if self.top_n else reranked


def build_rerank_compressor(settings: Settings | None = None, top_n: int | None = None) -> Qwen3RerankCompressor:
    settings = settings or get_settings()
    provider_name = settings.rerank_provider.strip().lower()
    if provider_name != "qwen3_local":
        raise ValueError(f"Unsupported rerank_provider: {settings.rerank_provider}")

    cache_key = (
        settings.rerank_model_path,
        settings.rerank_device,
        settings.rerank_batch_size,
        settings.rerank_max_length,
    )
    reranker = _RERANKER_CACHE.get(cache_key)
    if reranker is None:
        with _RERANKER_CACHE_LOCK:
            reranker = _RERANKER_CACHE.get(cache_key)
            if reranker is None:
                reranker = Qwen3LocalReranker(settings)
                _RERANKER_CACHE[cache_key] = reranker
    return Qwen3RerankCompressor(reranker=reranker, top_n=top_n)
